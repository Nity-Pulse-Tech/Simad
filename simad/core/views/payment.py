import logging

from django.views.generic import TemplateView
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from simad.users.models import Address
from simad.orders.models import Order

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

class PaymentSuccessView(TemplateView):
    template_name = "pages/home/payments/payment_succes.html"

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
