from django.contrib import admin

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
        "reference", "user", "order_type", "status", "total", "is_paid", "created",
    ]
    list_filter = ["status", "order_type", "is_paid"]
    search_fields = ["reference", "user__email", "user__phone_number"]
    readonly_fields = ["created", "modified"]
    inlines = [OrderItemInline]
    fieldsets = (
        ("Order Info", {
            "fields": ("user", "reference", "order_type", "status", "shipping_address"),
        }),
        ("Pricing", {
            "fields": ("subtotal", "discount_amount", "shipping_cost", "total"),
        }),
        ("Details", {
            "fields": ("note", "coupon_code", "is_paid"),
        }),
        ("Timestamps", {
            "fields": ("created", "modified"),
            "classes": ("collapse",),
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["order", "product_name", "quantity", "unit_price", "discount"]
    search_fields = ["order__reference", "product_name"]
    readonly_fields = ["created", "modified"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "reference", "order", "user", "method", "status", "amount",
        "currency", "paid_at", "created",
    ]
    list_filter = ["method", "status", "currency"]
    search_fields = ["reference", "order__reference", "user__email", "phone_number"]
    readonly_fields = ["created", "modified", "gateway_response"]
    fieldsets = (
        ("Payment Info", {
            "fields": ("order", "user", "reference", "method", "status"),
        }),
        ("Amount", {
            "fields": ("amount", "currency", "phone_number", "paid_at"),
        }),
        ("Gateway", {
            "fields": ("gateway_response",),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created", "modified"),
            "classes": ("collapse",),
        }),
    )


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
