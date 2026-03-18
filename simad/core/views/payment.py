from django.views.generic import TemplateView

class CartView(TemplateView):
    template_name = "pages/home/payments/cart.html"

from simad.orders.models import Order

class OrderSummaryView(TemplateView):
    template_name = "pages/home/payments/order_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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

class PaymentView(TemplateView):
    template_name = "pages/home/payments/payment.html"

class PaymentSuccessView(TemplateView):
    template_name = "pages/home/payments/payment_succes.html"

class PaymentFailureView(TemplateView):
    template_name = "pages/home/payments/payment_failure.html"
