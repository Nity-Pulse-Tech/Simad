from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from simad.global_data.enum import OrderStatusChoices
from simad.global_data.enum import PaymentStatusChoices
from .models import Cart
from .models import CartItem
from .models import Delivery
from .models import DeliveryTracking
from .models import Order
from .models import OrderAnalytics
from .models import OrderItem
from .models import Payment
from .models import ProductView


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ["product", "quantity", "unit_price"]
    readonly_fields = ["unit_price"]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ["product", "product_name", "quantity", "unit_price", "discount"]
    readonly_fields = ["product_name"]


class DeliveryTrackingInline(admin.TabularInline):
    model = DeliveryTracking
    extra = 0
    fields = ["status", "location", "description", "timestamp"]
    readonly_fields = ["timestamp"]


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ["reference", "method", "status", "amount", "paid_at"]
    readonly_fields = ["reference", "method", "amount", "paid_at"]
    can_delete = False


class DeliveryInline(admin.StackedInline):
    model = Delivery
    extra = 0
    fields = ["method", "status", "tracking_number", "carrier_name", "estimated_delivery_date"]
    can_delete = False


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["user", "coupon_code", "created", "modified"]
    search_fields = ["user__email", "user__phone_number"]
    readonly_fields = ["created", "modified"]
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["cart", "product", "quantity", "unit_price", "created"]
    search_fields = ["cart__user__email", "product__name"]
    readonly_fields = ["created", "modified"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "reference", "user_display", "order_type", "status", "total_display", "is_paid", "created",
    ]
    list_filter = ["status", "order_type", "is_paid", "created"]
    search_fields = ["reference", "user__email", "user__phone_number", "user__first_name", "user__last_name"]
    readonly_fields = ["reference", "created", "modified"]
    inlines = [OrderItemInline, PaymentInline, DeliveryInline]
    actions = ["mark_as_confirmed", "mark_as_shipped", "mark_as_delivered", "mark_as_cancelled"]
    
    fieldsets = (
        ("Order Context", {
            "fields": ("user", "reference", "order_type", "status"),
        }),
        ("Fulfillment", {
            "fields": ("shipping_address",),
        }),
        ("Financials", {
            "fields": ("subtotal", "discount_amount", "shipping_cost", "total", "is_paid"),
        }),
        ("Customer Notes", {
            "fields": ("note", "coupon_code"),
        }),
        ("Metadata", {
            "fields": ("created", "modified"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("Customer"))
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.full_name} ({obj.user.email})"
        return _("Guest / Deleted")

    @admin.display(description=_("Total"))
    def total_display(self, obj):
        return f"{obj.total} {obj.payments.first().currency if obj.payments.exists() else 'XOF'}"

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj and obj.status in [OrderStatusChoices.DELIVERED, OrderStatusChoices.CANCELLED]:
            readonly.extend(["status", "subtotal", "discount_amount", "shipping_cost", "total", "is_paid", "shipping_address"])
        return readonly

    @admin.action(description=_("Mark selected orders as Confirmed"))
    def mark_as_confirmed(self, request, queryset):
        queryset.update(status=OrderStatusChoices.CONFIRMED)

    @admin.action(description=_("Mark selected orders as Shipped"))
    def mark_as_shipped(self, request, queryset):
        queryset.update(status=OrderStatusChoices.SHIPPED)

    @admin.action(description=_("Mark selected orders as Delivered"))
    def mark_as_delivered(self, request, queryset):
        for order in queryset:
            order.status = OrderStatusChoices.DELIVERED
            order.save()
            # Also update delivery status if it exists
            if hasattr(order, 'delivery'):
                order.delivery.status = "DELIVERED"
                order.delivery.delivered_at = timezone.now()
                order.delivery.save()

    @admin.action(description=_("Mark selected orders as Cancelled"))
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status=OrderStatusChoices.CANCELLED)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["order", "product_name", "quantity", "unit_price", "discount"]
    search_fields = ["order__reference", "product_name"]
    readonly_fields = ["created", "modified"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "reference", "order", "user", "method", "provider", "status", "amount_display",
        "paid_at", "created",
    ]
    list_filter = ["method", "status", "currency", "created"]
    search_fields = ["reference", "order__reference", "user__email", "phone_number"]
    readonly_fields = ["reference", "order", "user", "amount", "currency", "gateway_response", "created", "modified"]
    actions = ["mark_as_paid", "mark_as_failed"]
    
    fieldsets = (
        ("Transaction Details", {
            "fields": ("order", "user", "reference", "method", "provider", "status"),
        }),
        ("Financial Data", {
            "fields": ("amount", "currency", "phone_number", "paid_at"),
        }),
        ("Stripe Info", {
            "fields": ("stripe_payment_intent_id", "stripe_checkout_session_id", "webhook_events"),
            "classes": ("collapse",),
        }),
        ("Gateway Feedback", {
            "fields": ("gateway_response", "metadata"),
            "classes": ("collapse",),
        }),
        ("Metadata", {
            "fields": ("created", "modified"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("Amount"))
    def amount_display(self, obj):
        return f"{obj.amount} {obj.currency}"

    @admin.action(description=_("Mark selected payments as Paid"))
    def mark_as_paid(self, request, queryset):
        queryset.update(status=PaymentStatusChoices.SUCCEEDED, paid_at=timezone.now())
        for payment in queryset:
            if payment.order:
                payment.order.is_paid = True
                payment.order.save()

    @admin.action(description=_("Mark selected payments as Failed"))
    def mark_as_failed(self, request, queryset):
        queryset.update(status=PaymentStatusChoices.FAILED)


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = [
        "order", "method", "status", "tracking_number", "carrier_name",
        "estimated_delivery_date", "delivered_at",
    ]
    list_filter = ["method", "status"]
    search_fields = ["order__reference", "tracking_number", "carrier_name"]
    readonly_fields = ["created", "modified"]
    inlines = [DeliveryTrackingInline]


@admin.register(DeliveryTracking)
class DeliveryTrackingAdmin(admin.ModelAdmin):
    list_display = ["delivery", "status", "location", "timestamp"]
    list_filter = ["status"]
    search_fields = ["delivery__order__reference", "location"]
    readonly_fields = ["timestamp"]


@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = ["product", "user", "ip_address", "viewed_at"]
    list_filter = ["viewed_at"]
    search_fields = ["product__name", "user__email", "ip_address"]
    readonly_fields = ["viewed_at", "created", "modified"]


@admin.register(OrderAnalytics)
class OrderAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        "date", "total_orders", "total_revenue", "total_items_sold",
        "cancelled_orders", "refunded_orders", "new_customers", "average_order_value",
    ]
    list_filter = ["date"]
    readonly_fields = ["created", "modified"]
    ordering = ["-date"]
