from django.views.generic import TemplateView
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from simad.users.models import Address
from simad.orders.models import Order

class CartView(TemplateView):
    template_name = "pages/home/payments/cart.html"

class OrderSummaryView(TemplateView):
    template_name = "pages/home/payments/order_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add addresses if user is authenticated
        if user.is_authenticated:
            context['addresses'] = user.addresses.all().order_by('-is_default', '-created')
        else:
            context['addresses'] = []

        # Retrieve from session
        order_ref = self.request.session.get('order_ref')
        if not order_ref:
            order_ref = self.request.GET.get('ref')
            
        if order_ref:
            try:
                order = Order.objects.prefetch_related('items__product').get(reference=order_ref)
                context['order'] = order
                context['items'] = order.items.all()
            except Order.DoesNotExist:
                context['order'] = None
        else:
            context['order'] = None
        return context

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login') # Should not happen with LoginRequired but safe
            
        order_ref = request.session.get('order_ref') or request.POST.get('order_ref')
        if not order_ref:
            messages.error(request, "Order session expired. Please start over.")
            return redirect('core:cart')
            
        try:
            order = Order.objects.get(reference=order_ref)
            address_id = request.POST.get('address_id')
            
            if address_id:
                # User selected an existing address
                address = get_object_or_404(Address, id=address_id, user=request.user)
                order.shipping_address = address
                order.save()
                return redirect('core:payment')
            else:
                # User is submitting a NEW address form from checkout
                # (Optional: we can also handle this via the JS modal we built)
                messages.error(request, "Please select or add a delivery address.")
                return self.get(request, *args, **kwargs)
                
        except Order.DoesNotExist:
            messages.error(request, "Order not found.")
            return redirect('core:cart')

class PaymentView(TemplateView):
    template_name = "pages/home/payments/payment.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_ref = self.request.session.get('order_ref')
        print(f"DEBUG: PaymentView - Retrieved order_ref from session: {order_ref}")
        
        if not order_ref:
            order_ref = self.request.GET.get('ref')
            
        if order_ref:
            try:
                order = Order.objects.prefetch_related('items__product').get(reference=order_ref)
                context['order'] = order
                context['items'] = order.items.all()
            except Order.DoesNotExist:
                context['order'] = None
        return context

class PaymentSuccessView(TemplateView):
    template_name = "pages/home/payments/payment_succes.html"

class PaymentFailureView(TemplateView):
    template_name = "pages/home/payments/payment_failure.html"
