import logging
import uuid
from django.views.generic import TemplateView
from django.conf import settings
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from simad.users.models import Address
from simad.orders.models import Order, Payment
from simad.global_data.enum import PaymentMethodChoices, PaymentStatusChoices
from simad.payments.services import PayUnitService, StripeService
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.utils import timezone

logger = logging.getLogger(__name__)

class CartView(TemplateView):
    template_name = "pages/home/payments/cart.html"

    def get(self, request, *args, **kwargs):
        logger.info(
            "CartView GET — user=%s, IP=%s",
            request.user if request.user.is_authenticated else "Anonymous",
            request.META.get("REMOTE_ADDR"),
        )
        return super().get(request, *args, **kwargs)

class OrderSummaryView(TemplateView):
    template_name = "pages/home/payments/order_summary.html"

    def get_context_data(self, **kwargs):
        logger.info("OrderSummaryView.get_context_data() called")
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Add addresses if user is authenticated
        if user.is_authenticated:
            addresses = user.addresses.all().order_by('-is_default', '-created')
            context['addresses'] = addresses
            logger.info("Loaded %d addresses for user %s", addresses.count(), user.email)
        else:
            context['addresses'] = []
            logger.info("Anonymous user — no addresses loaded")

        # Retrieve from session
        order_ref = self.request.session.get('order_ref')
        logger.debug("order_ref from session: %s", order_ref)
        if not order_ref:
            order_ref = self.request.GET.get('ref')
            logger.debug("order_ref from GET param: %s", order_ref)

        if order_ref:
            try:
                order = Order.objects.prefetch_related('items__product').get(reference=order_ref)
                context['order'] = order
                context['items'] = order.items.all()
                logger.info(
                    "Loaded order %s — %d items, total=%s, status=%s",
                    order.reference,
                    order.items.count(),
                    order.total,
                    order.status,
                )
            except Order.DoesNotExist:
                context['order'] = None
                logger.warning("Order with reference '%s' does not exist", order_ref)
        else:
            context['order'] = None
            logger.warning("No order_ref found in session or GET params")
        return context

    def get(self, request, *args, **kwargs):
        logger.info(
            "OrderSummaryView GET — user=%s, session_key=%s",
            request.user if request.user.is_authenticated else "Anonymous",
            request.session.session_key,
        )
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        logger.info(
            "OrderSummaryView POST — user=%s, POST data keys=%s",
            request.user if request.user.is_authenticated else "Anonymous",
            list(request.POST.keys()),
        )

        if not request.user.is_authenticated:
            logger.warning("Unauthenticated user attempted POST on OrderSummaryView")
            return redirect('login')  # Should not happen with LoginRequired but safe

        order_ref = request.session.get('order_ref') or request.POST.get('order_ref')
        logger.info("POST order_ref resolved to: %s", order_ref)

        if not order_ref:
            logger.error("Order session expired — no order_ref found")
            messages.error(request, "Order session expired. Please start over.")
            return redirect('core:cart')

        try:
            order = Order.objects.get(reference=order_ref)
            address_id = request.POST.get('address_id')
            logger.info("Order %s found, address_id from POST: %s", order_ref, address_id)

            if address_id:
                # User selected an existing address
                address = get_object_or_404(Address, id=address_id, user=request.user)
                order.shipping_address = address
                order.save()
                logger.info(
                    "Shipping address set to %s for order %s — redirecting to payment",
                    address_id,
                    order_ref,
                )
                return redirect('core:payment')
            else:
                # User is submitting a NEW address form from checkout
                logger.warning("No address_id provided for order %s", order_ref)
                messages.error(request, "Please select or add a delivery address.")
                return self.get(request, *args, **kwargs)

        except Order.DoesNotExist:
            logger.error("Order '%s' not found during POST", order_ref)
            messages.error(request, "Order not found.")
            return redirect('core:cart')

class PaymentView(TemplateView):
    template_name = "pages/home/payments/payment.html"

    def get(self, request, *args, **kwargs):
        logger.info(
            "PaymentView GET — user=%s, session_key=%s",
            request.user if request.user.is_authenticated else "Anonymous",
            request.session.session_key,
        )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        logger.info("PaymentView.get_context_data() called")
        context = super().get_context_data(**kwargs)
        order_ref = self.request.session.get('order_ref')
        logger.info("PaymentView — order_ref from session: %s", order_ref)

        if not order_ref:
            order_ref = self.request.GET.get('ref')
            logger.debug("PaymentView — order_ref from GET param: %s", order_ref)

        if order_ref:
            try:
                order = Order.objects.prefetch_related('items__product').get(reference=order_ref)
                context['order'] = order
                context['items'] = order.items.all()
                logger.info(
                    "PaymentView — loaded order %s: %d items, subtotal=%s, total=%s, is_paid=%s",
                    order.reference,
                    order.items.count(),
                    order.subtotal,
                    order.total,
                    order.is_paid,
                )
            except Order.DoesNotExist:
                context['order'] = None
                logger.error("PaymentView — order '%s' does not exist", order_ref)
        else:
            logger.warning("PaymentView — no order_ref available")
        return context

    def post(self, request, *args, **kwargs):
        logger.info("PaymentView POST — user=%s", request.user)
        
        order_ref = request.session.get('order_ref')
        if not order_ref:
            messages.error(request, "Order session expired.")
            return redirect('core:cart')
            
        order = get_object_or_404(Order, reference=order_ref)
        payment_method = request.POST.get('payment_method')
        
        if payment_method == 'cod':
            # Handle Cash on Delivery
            payment = Payment.objects.create(
                order=order,
                user=request.user,
                reference=f"PAY-{uuid.uuid4().hex[:8].upper()}",
                method=PaymentMethodChoices.CASH_ON_DELIVERY,
                status=PaymentStatusChoices.PENDING,
                amount=order.total,
                currency="XAF"
            )
            order.status = "PROCESSING"

            # Generate QR Code
            now = timezone.now()
            items_summary = "\n".join([f"- {item.product_name} (x{item.quantity})" for item in order.items.all()])
            qr_data = (
                f"ORDER SUMMARY\n"
                f"Order ID: {order.reference}\n"
                f"Date: {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Items:\n{items_summary}\n\n"
                f"Total: {order.total} XAF"
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            file_name = f"qr_{order.reference}_{now.strftime('%Y%m%d%H%M%S')}.png"
            order.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=False)
            
            order.save()
            return redirect('core:payment-success')
            
        elif payment_method in ['mtn_momo', 'orange_money']:
            phone_number = request.POST.get(f"{payment_method.split('_')[0]}_phone")
            if not phone_number:
                messages.error(request, "Please provide a phone number.")
                return self.get(request, *args, **kwargs)
                
            # Create Payment record
            payment_ref = f"PU-{uuid.uuid4().hex[:12].upper()}"
            payment = Payment.objects.create(
                order=order,
                user=request.user,
                reference=payment_ref,
                method=PaymentMethodChoices.MOBILE_MONEY,
                status=PaymentStatusChoices.PENDING,
                amount=order.total,
                currency="XAF",
                phone_number=phone_number
            )
            
            # Initialize PayUnit Direct Payment
            payunit = PayUnitService()
            notify_url = getattr(settings, "PAYUNIT_NOTIFY_URL", "")
            return_url = request.build_absolute_uri(reverse('core:payment-success'))
            payment_network = "MTN" if payment_method == 'mtn_momo' else "ORANGE"
            
            result = payunit.make_direct_payment(
                total_amount=order.total,
                transaction_id=payment_ref,
                phone_number=phone_number,
                payment_network=payment_network,
                notify_url=notify_url,
                return_url=return_url,
                currency="XAF"
            )
            
            if result['success']:
                payment.gateway_response = result['data']
                payment.save()
                messages.success(request, result['message'])
                # Redirect to success page or stay on page with instructions
                return redirect('core:payment-success')
            else:
                payment.status = PaymentStatusChoices.FAILED
                payment.gateway_response = result.get('data', {})
                payment.save()
                messages.error(request, f"Payment failed: {result['message']}")
                return self.get(request, *args, **kwargs)
        
        elif payment_method == 'card':
            # Handle Stripe Payment
            stripe_service = StripeService()
            # Stripe amount is in integer subunits (XAF is zero-decimal, so amount is base amount)
            amount = int(order.total)
            
            # Create a pending Payment record
            payment_ref = f"ST-{uuid.uuid4().hex[:12].upper()}"
            payment = Payment.objects.create(
                order=order,
                user=request.user,
                reference=payment_ref,
                method=PaymentMethodChoices.CREDIT_CARD,
                status=PaymentStatusChoices.PENDING,
                amount=order.total,
                currency="XAF"
            )
            
            result = stripe_service.create_payment_intent(
                amount=amount,
                currency="XAF",
                metadata={
                    "order_reference": order.reference,
                    "payment_reference": payment_ref,
                    "user_email": request.user.email if request.user.is_authenticated else ""
                }
            )
            
            if result['success']:
                payment.gateway_response = {"intent_id": result['intent_id']}
                payment.save()
                
                context = self.get_context_data(**kwargs)
                context.update({
                    'client_secret': result['client_secret'],
                    'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
                    'payment_method': 'card'
                })
                # We return the same page but with the client_secret to trigger the Stripe confirm flow
                from django.shortcuts import render
                return render(request, self.template_name, context)
            else:
                payment.status = PaymentStatusChoices.FAILED
                payment.gateway_response = result
                payment.save()
                messages.error(request, f"Stripe Error: {result['message']}")
                return self.get(request, *args, **kwargs)
        
        else:
            messages.error(request, "Please select a valid payment method.")
            return self.get(request, *args, **kwargs)

class PaymentSuccessView(TemplateView):
    template_name = "pages/home/payments/payment_succes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_ref = self.request.session.get('order_ref')
        if order_ref:
            try:
                order = Order.objects.prefetch_related('items__product').get(reference=order_ref)
                context['order'] = order
                context['items'] = order.items.all()
                logger.info("PaymentSuccessView — loaded order %s for display", order_ref)
            except Order.DoesNotExist:
                logger.error("PaymentSuccessView — order '%s' not found", order_ref)
        return context

    def get(self, request, *args, **kwargs):
        logger.info(
            "PaymentSuccessView GET — user=%s, IP=%s",
            request.user if request.user.is_authenticated else "Anonymous",
            request.META.get("REMOTE_ADDR"),
        )
        return super().get(request, *args, **kwargs)

class PaymentFailureView(TemplateView):
    template_name = "pages/home/payments/payment_failure.html"

    def get(self, request, *args, **kwargs):
        logger.warning(
            "PaymentFailureView GET — user=%s, IP=%s",
            request.user if request.user.is_authenticated else "Anonymous",
            request.META.get("REMOTE_ADDR"),
        )
        return super().get(request, *args, **kwargs)
