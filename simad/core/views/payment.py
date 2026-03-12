from django.views.generic import TemplateView

class CartView(TemplateView):
    template_name = "pages/home/payments/cart.html"

class OrderSummaryView(TemplateView):
    template_name = "pages/home/payments/order_summary.html"

class PaymentView(TemplateView):
    template_name = "pages/home/payments/payment.html"

class PaymentSuccessView(TemplateView):
    template_name = "pages/home/payments/payment_succes.html"

class PaymentFailureView(TemplateView):
    template_name = "pages/home/payments/payment_failure.html"
