import json
import logging

from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.db.models import Sum
from django.views import View

from simad.users.models import Address, UserProfile
from simad.global_data.enum import OrderStatusChoices
from simad.catalog.models import Wishlist
from simad.orders.models import Order

logger = logging.getLogger(__name__)

class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/dashboard.html"

    def get(self, request, *args, **kwargs):
        logger.info(
            "UserDashboardView GET — user=%s, IP=%s",
            request.user.email,
            request.META.get("REMOTE_ADDR"),
        )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        logger.info("UserDashboardView.get_context_data() called")
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Dashboard KPIs
        total_orders = user.orders.count()
        pending_quotes = user.orders.filter(status=OrderStatusChoices.PENDING).count()
        total_spent = user.orders.filter(is_paid=True).aggregate(Sum('total'))['total__sum'] or 0
        favorites_count = Wishlist.objects.filter(user=user).count()

        context['total_orders'] = total_orders
        context['pending_quotes'] = pending_quotes
        context['total_spent'] = total_spent
        context['favorites_count'] = favorites_count

        logger.info(
            "Dashboard KPIs for %s — total_orders=%d, pending=%d, total_spent=%s, favorites=%d",
            user.email,
            total_orders,
            pending_quotes,
            total_spent,
            favorites_count,
        )

        # Recent Orders (Top 5)
        recent_orders = user.orders.all().order_by('-created')[:5]
        context['recent_orders'] = recent_orders
        logger.info("Loaded %d recent orders for user %s", len(recent_orders), user.email)

        # Default Address
        default_address = user.addresses.filter(is_default=True).first()
        context['default_address'] = default_address
        logger.info(
            "Default address for %s: %s",
            user.email,
            default_address.city if default_address else "None",
        )

        return context

class MyOrderView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/pages/my_order.html"

    def get(self, request, *args, **kwargs):
        logger.info("MyOrderView GET — user=%s", request.user.email)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders = self.request.user.orders.all().order_by('-created')
        context['orders'] = orders
        logger.info("MyOrderView — loaded %d orders for user %s", orders.count(), self.request.user.email)
        return context

class OrderDetailView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/pages/order_detail.html"

    def get(self, request, *args, **kwargs):
        logger.info(
            "OrderDetailView GET — user=%s, order_pk=%s",
            request.user.email,
            kwargs.get('pk'),
        )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.kwargs.get('pk')
        order = get_object_or_404(Order, id=order_id, user=self.request.user)
        context['order'] = order
        logger.info(
            "OrderDetailView — order ref=%s, status=%s, total=%s, items=%d, user=%s",
            order.reference,
            order.status,
            order.total,
            order.items.count(),
            self.request.user.email,
        )
        return context

class MyInvoiceView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/pages/my_invoice.html"

    def get(self, request, *args, **kwargs):
        logger.info("MyInvoiceView GET — user=%s", request.user.email)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Invoices are basically paid orders in this context
        invoices = user.orders.filter(is_paid=True).order_by('-created')
        context['invoices'] = invoices

        # Stats
        total_spent = invoices.aggregate(Sum('total'))['total__sum'] or 0
        context['total_spent'] = total_spent

        # Outstanding (Pending orders total)
        outstanding = user.orders.filter(is_paid=False).aggregate(Sum('total'))['total__sum'] or 0
        context['outstanding'] = outstanding

        logger.info(
            "MyInvoiceView — user=%s, paid_invoices=%d, total_spent=%s, outstanding=%s",
            user.email,
            invoices.count(),
            total_spent,
            outstanding,
        )
        return context

class FavoritesView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/pages/favorites.html"

    def get(self, request, *args, **kwargs):
        logger.info("FavoritesView GET — user=%s", request.user.email)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        favorites = Wishlist.objects.filter(user=self.request.user).select_related('product')
        context['favorites'] = favorites
        logger.info(
            "FavoritesView — loaded %d favorites for user %s",
            favorites.count(),
            self.request.user.email,
        )
        return context

class AddressView(LoginRequiredMixin, View):
    template_name = "pages/user_dashboard/pages/address.html"

    def get(self, request, *args, **kwargs):
        addresses = request.user.addresses.all().order_by('-is_default', '-created')
        logger.info(
            "AddressView GET — user=%s, address_count=%d",
            request.user.email,
            addresses.count(),
        )
        return render(request, self.template_name, {"addresses": addresses})

    def post(self, request, *args, **kwargs):
        logger.info(
            "AddressView POST — user=%s, content_type=%s",
            request.user.email,
            request.content_type,
        )
        try:
            data = json.loads(request.body)
            action = data.get('action')
            logger.info("AddressView POST action='%s' by user %s", action, request.user.email)

            if action == 'create':
                address = Address.objects.create(
                    user=request.user,
                    address_line1=data.get('address_line1', ''),
                    address_line2=data.get('address_line2', ''),
                    city=data.get('city', ''),
                    state_province=data.get('state_province', ''),
                    postal_code=data.get('postal_code', ''),
                    country=data.get('country', ''),
                    is_default=data.get('is_default', False)
                )
                if address.is_default:
                    request.user.addresses.exclude(id=address.id).update(is_default=False)
                logger.info(
                    "Address CREATED — id=%s, city=%s, is_default=%s, user=%s",
                    address.id,
                    address.city,
                    address.is_default,
                    request.user.email,
                )
                return JsonResponse({"status": "success", "message": "Address created successfully."})

            elif action == 'update':
                address_id = data.get('id')
                address = get_object_or_404(Address, id=address_id, user=request.user)
                logger.info("Updating address id=%s for user %s", address_id, request.user.email)
                address.address_line1 = data.get('address_line1', address.address_line1)
                address.address_line2 = data.get('address_line2', address.address_line2)
                address.city = data.get('city', address.city)
                address.state_province = data.get('state_province', address.state_province)
                address.postal_code = data.get('postal_code', address.postal_code)
                address.country = data.get('country', address.country)
                address.is_default = data.get('is_default', address.is_default)
                address.save()
                if address.is_default:
                    request.user.addresses.exclude(id=address.id).update(is_default=False)
                logger.info(
                    "Address UPDATED — id=%s, city=%s, is_default=%s",
                    address.id,
                    address.city,
                    address.is_default,
                )
                return JsonResponse({"status": "success", "message": "Address updated successfully."})

            elif action == 'delete':
                address_id = data.get('id')
                address = get_object_or_404(Address, id=address_id, user=request.user)
                address.delete()
                logger.info("Address DELETED — id=%s, user=%s", address_id, request.user.email)
                return JsonResponse({"status": "success", "message": "Address deleted successfully."})

            logger.warning("AddressView — invalid action '%s'", action)
            return JsonResponse({"status": "error", "message": "Invalid action."}, status=400)
        except json.JSONDecodeError as e:
            logger.error("AddressView — invalid JSON body: %s", e)
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
        except Exception as e:
            logger.exception("AddressView — unexpected error: %s", e)
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

class ProfileView(LoginRequiredMixin, View):
    template_name = "pages/user_dashboard/pages/profile.html"

    def get(self, request):
        logger.info("ProfileView GET — user=%s", request.user.email)
        return render(request, self.template_name)

    def post(self, request):
        user = request.user
        logger.info(
            "ProfileView POST — user=%s, POST keys=%s, FILES keys=%s",
            user.email,
            list(request.POST.keys()),
            list(request.FILES.keys()),
        )

        # 1. Update basic info (Full Name)
        full_name = request.POST.get("full_name", "").strip()
        if full_name and full_name != user.full_name:
            parts = full_name.split(" ", 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ""
            user.save(update_fields=["first_name", "last_name"])
            logger.info("Profile name updated for %s: '%s'", user.email, full_name)
            messages.success(request, "Profile updated successfully.")

        # 2. Handle Avatar Upload
        avatar = request.FILES.get("avatar")
        if avatar:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.avatar = avatar
            profile.save(update_fields=["avatar"])
            logger.info("Avatar updated for user %s — filename=%s", user.email, avatar.name)
            messages.success(request, "Avatar updated successfully.")

        # 3. Handle Password Change
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if current_password or new_password or confirm_password:
            logger.info("Password change attempt for user %s", user.email)
            if not user.check_password(current_password):
                logger.warning("Password change FAILED for %s — incorrect current password", user.email)
                messages.error(request, "Incorrect current password.")
            elif new_password != confirm_password:
                logger.warning("Password change FAILED for %s — passwords don't match", user.email)
                messages.error(request, "New passwords do not match.")
            elif len(new_password) < 8:
                logger.warning("Password change FAILED for %s — too short", user.email)
                messages.error(request, "New password must be at least 8 characters.")
            else:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)
                logger.info("Password changed successfully for user %s", user.email)
                messages.success(request, "Password changed successfully.")

class MyQRCodesView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/pages/my_qr_codes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders_with_qr = self.request.user.orders.filter(qr_code__isnull=False).exclude(qr_code='').order_by('-created')
        context['orders'] = orders_with_qr
        logger.info("MyQRCodesView — loaded %d orders with QR codes for user %s", orders_with_qr.count(), self.request.user.email)
        return context
