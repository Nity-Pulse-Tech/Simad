from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/dashboard.html"

class MyOrderView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/pages/my_order.html"

class MyInvoiceView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/pages/my_invoice.html"

class AddressView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/pages/address.html"

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/pages/profile.html"
