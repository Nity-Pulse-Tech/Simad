from django.db import models
from django.utils.translation import gettext_lazy as _

from simad.core.models import SIMADBASEMODEL
from simad.global_data.enum import DeliveryMethodChoices
from simad.global_data.enum import DeliveryStatusChoices
from simad.global_data.enum import OrderStatusChoices
from simad.global_data.enum import OrderTypeChoices
from simad.global_data.enum import PaymentMethodChoices
from simad.global_data.enum import PaymentStatusChoices
from simad.users.models import Address
from simad.users.models import User


# ──────────────────────────────────────────────
# Cart
# ──────────────────────────────────────────────

class Cart(SIMADBASEMODEL):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="cart"
    )
    note = models.TextField(_("Note"), blank=True)
    coupon_code = models.CharField(_("Coupon Code"), max_length=50, blank=True)

    class Meta:
        verbose_name = _("Cart")
        verbose_name_plural = _("Carts")

    def __str__(self):
        return f"Cart of {self.user}"

    @property
    def total(self) -> "models.DecimalField":
        return sum(item.subtotal for item in self.items.all())


class CartItem(SIMADBASEMODEL):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    # Lazy import via string reference to avoid circular import
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.CASCADE, related_name="cart_items"
    )
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)
    unit_price = models.DecimalField(
        _("Unit Price at Time of Add"), max_digits=12, decimal_places=2
    )

    class Meta:
        verbose_name = _("Cart Item")
        verbose_name_plural = _("Cart Items")
        unique_together = [("cart", "product")]

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"

    @property
    def subtotal(self):
        return self.quantity * self.unit_price


# ──────────────────────────────────────────────
# Order
# ──────────────────────────────────────────────

class Order(SIMADBASEMODEL):
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="orders"
    )
    reference = models.CharField(_("Reference"), max_length=64, unique=True, default="")
    order_type = models.CharField(
        _("Order Type"),
        max_length=20,
        choices=OrderTypeChoices.choices,
        default=OrderTypeChoices.STANDARD,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=OrderStatusChoices.choices,
        default=OrderStatusChoices.PENDING,
    )
    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    subtotal = models.DecimalField(
        _("Subtotal"), max_digits=12, decimal_places=2, default=0
    )
    discount_amount = models.DecimalField(
        _("Discount"), max_digits=12, decimal_places=2, default=0
    )
    shipping_cost = models.DecimalField(
        _("Shipping Cost"), max_digits=12, decimal_places=2, default=0
    )
    total = models.DecimalField(
        _("Total"), max_digits=12, decimal_places=2, default=0
    )
    note = models.TextField(_("Customer Note"), blank=True)
    coupon_code = models.CharField(_("Coupon Code"), max_length=50, blank=True)
    is_paid = models.BooleanField(_("Paid"), default=False)

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ["-created"]

    def __str__(self):
        return f"Order {self.reference}"


class OrderItem(SIMADBASEMODEL):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.SET_NULL, null=True, related_name="order_items"
    )
    product_name = models.CharField(_("Product Name at Order"), max_length=255, default="")
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)
    unit_price = models.DecimalField(
        _("Unit Price at Order"), max_digits=12, decimal_places=2
    )
    discount = models.DecimalField(
        _("Item Discount"), max_digits=12, decimal_places=2, default=0
    )

    class Meta:
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")

    def __str__(self):
        return f"{self.quantity} × {self.product_name}"

    @property
    def subtotal(self):
        return (self.quantity * self.unit_price) - self.discount


# ──────────────────────────────────────────────
# Payment
# ──────────────────────────────────────────────

class Payment(SIMADBASEMODEL):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="payments"
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="payments"
    )
    reference = models.CharField(_("Payment Reference"), max_length=100, unique=True, default="")
    method = models.CharField(
        _("Payment Method"),
        max_length=30,
        choices=PaymentMethodChoices.choices,
        default=PaymentMethodChoices.MOBILE_MONEY,
    )
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=PaymentStatusChoices.choices,
        default=PaymentStatusChoices.PENDING,
    )
    amount = models.DecimalField(_("Amount"), max_digits=12, decimal_places=2)
    currency = models.CharField(_("Currency"), max_length=10, default="XOF")
    phone_number = models.CharField(
        _("Mobile Money Phone"), max_length=20, blank=True
    )
    gateway_response = models.JSONField(
        _("Gateway Response"), default=dict, blank=True
    )
    paid_at = models.DateTimeField(_("Paid At"), null=True, blank=True)

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
        ordering = ["-created"]

    def __str__(self):
        return f"Payment {self.reference} – {self.status}"


# ──────────────────────────────────────────────
# Delivery
# ──────────────────────────────────────────────

class Delivery(SIMADBASEMODEL):
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="delivery"
    )
    method = models.CharField(
        _("Delivery Method"),
        max_length=20,
        choices=DeliveryMethodChoices.choices,
        default=DeliveryMethodChoices.STANDARD,
    )
    status = models.CharField(
        _("Delivery Status"),
        max_length=30,
        choices=DeliveryStatusChoices.choices,
        default=DeliveryStatusChoices.PENDING,
    )
    tracking_number = models.CharField(_("Tracking Number"), max_length=100, blank=True, default="")
    carrier_name = models.CharField(_("Carrier Name"), max_length=100, blank=True, default="")
    estimated_delivery_date = models.DateField(
        _("Estimated Delivery Date"), null=True, blank=True
    )
    delivered_at = models.DateTimeField(_("Delivered At"), null=True, blank=True)
    delivery_cost = models.DecimalField(
        _("Delivery Cost"), max_digits=10, decimal_places=2, default=0
    )
    notes = models.TextField(_("Delivery Notes"), blank=True)

    class Meta:
        verbose_name = _("Delivery")
        verbose_name_plural = _("Deliveries")
        ordering = ["-created"]

    def __str__(self):
        return f"Delivery for Order {self.order.reference}"


class DeliveryTracking(SIMADBASEMODEL):
    delivery = models.ForeignKey(
        Delivery, on_delete=models.CASCADE, related_name="tracking_events"
    )
    status = models.CharField(
        _("Event Status"),
        max_length=30,
        choices=DeliveryStatusChoices.choices,
    )
    location = models.CharField(_("Location"), max_length=255, blank=True, default="")
    description = models.TextField(_("Description"), blank=True, default="")
    timestamp = models.DateTimeField(_("Event Timestamp"), auto_now_add=True)

    class Meta:
        verbose_name = _("Delivery Tracking Event")
        verbose_name_plural = _("Delivery Tracking Events")
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.status} @ {self.timestamp}"


# ──────────────────────────────────────────────
# Analytics
# ──────────────────────────────────────────────

class ProductView(SIMADBASEMODEL):
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.CASCADE, related_name="views"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product_views",
    )
    ip_address = models.GenericIPAddressField(_("IP Address"), null=True, blank=True)
    user_agent = models.TextField(_("User Agent"), blank=True)
    referrer = models.URLField(_("Referrer"), blank=True)
    viewed_at = models.DateTimeField(_("Viewed At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Product View")
        verbose_name_plural = _("Product Views")
        ordering = ["-viewed_at"]

    def __str__(self):
        return f"View: {self.product.name}"


class OrderAnalytics(SIMADBASEMODEL):
    date = models.DateField(_("Date"), unique=True)
    total_orders = models.PositiveIntegerField(_("Total Orders"), default=0)
    total_revenue = models.DecimalField(
        _("Total Revenue"), max_digits=16, decimal_places=2, default=0
    )
    total_items_sold = models.PositiveIntegerField(_("Total Items Sold"), default=0)
    cancelled_orders = models.PositiveIntegerField(_("Cancelled Orders"), default=0)
    refunded_orders = models.PositiveIntegerField(_("Refunded Orders"), default=0)
    new_customers = models.PositiveIntegerField(_("New Customers"), default=0)
    average_order_value = models.DecimalField(
        _("Average Order Value"), max_digits=12, decimal_places=2, default=0
    )

    class Meta:
        verbose_name = _("Order Analytics")
        verbose_name_plural = _("Order Analytics")
        ordering = ["-date"]

    def __str__(self):
        return f"Analytics {self.date}"
