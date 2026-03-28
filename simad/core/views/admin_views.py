from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/admin_dashboard.html"

class AdminDeliveriesView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/delivry_management.html"

class AdminPromotionsView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/promotion_and_flash_deal_managment.html"

class AdminAddProductView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/add_product.html"

class AdminProductListView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/product_management.html"

class AdminUsersView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/user_management.html"

class AdminCorporateSettingsView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/corporate_settings.html"

class AdminLegalPagesView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/legal_pages_management.html"
