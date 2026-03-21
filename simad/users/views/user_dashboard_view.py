from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from simad.users.models import UserProfile

class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/dashboard.html"

class MyOrderView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/pages/my_order.html"

class MyInvoiceView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/pages/my_invoice.html"

class AddressView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/pages/address.html"

class ProfileView(LoginRequiredMixin, View):
    template_name = "pages/user_dashboard/pages/profile.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        user = request.user
        
        # 1. Update basic info (Full Name)
        full_name = request.POST.get("full_name", "").strip()
        if full_name and full_name != user.full_name:
            parts = full_name.split(" ", 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ""
            user.save(update_fields=["first_name", "last_name"])
            messages.success(request, "Profile updated successfully.")

        # 2. Handle Avatar Upload
        avatar = request.FILES.get("avatar")
        if avatar:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.avatar = avatar
            profile.save(update_fields=["avatar"])
            messages.success(request, "Avatar updated successfully.")

        # 3. Handle Password Change
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if current_password or new_password or confirm_password:
            if not user.check_password(current_password):
                messages.error(request, "Incorrect current password.")
            elif new_password != confirm_password:
                messages.error(request, "New passwords do not match.")
            elif len(new_password) < 8:
                messages.error(request, "New password must be at least 8 characters.")
            else:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed successfully.")

        return redirect("users:profile")
