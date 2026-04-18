from django.db import models
from django.utils.translation import gettext_lazy as _


class GenderChoices(models.TextChoices):
    MALE = "MALE", _("Male")
    FEMALE = "FEMALE", _("Female")
    OTHER = "OTHER", _("Other")
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", _("Prefer not to say")


class UserTypeChoices(models.TextChoices):
    ADMIN = "ADMIN", _("Administrator")
    STAFF = "STAFF", _("Staff")
    CUSTOMER = "CUSTOMER", _("Customer")
    VENDOR = "VENDOR", _("Vendor")
    DELIVERY_AGENT = "DELIVERY_AGENT", _("Delivery Agent")


class AddressTypeChoices(models.TextChoices):
    HOME = "HOME", _("Home")
    OFFICE = "OFFICE", _("Office")
    SHIPPING = "SHIPPING", _("Shipping Address")
    BILLING = "BILLING", _("Billing Address")
    OTHER = "OTHER", _("Other")


class ProductTypeChoices(models.TextChoices):
    PHYSICAL = "PHYSICAL", _("Physical Product")
    DIGITAL = "DIGITAL", _("Digital Product")
    SERVICE = "SERVICE", _("Service")


class UnitOfMeasureChoices(models.TextChoices):
    PIECE = "PIECE", _("Piece")
    KILOGRAM = "KG", _("Kilogram")
    GRAM = "G", _("Gram")
    LITER = "L", _("Liter")
    MILLILITER = "ML", _("Milliliter")
    PACK = "PACK", _("Pack")
    BOX = "BOX", _("Box")


class OrderStatusChoices(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    CONFIRMED = "CONFIRMED", _("Confirmed")
    PROCESSING = "PROCESSING", _("Processing")
    SHIPPED = "SHIPPED", _("Shipped")
    DELIVERED = "DELIVERED", _("Delivered")
    CANCELLED = "CANCELLED", _("Cancelled")
    REFUNDED = "REFUNDED", _("Refunded")
    FAILED = "FAILED", _("Failed")


class OrderTypeChoices(models.TextChoices):
    STANDARD = "STANDARD", _("Standard Order")
    SUBSCRIPTION = "SUBSCRIPTION", _("Subscription Order")
    PRE_ORDER = "PRE_ORDER", _("Pre-Order")


class PaymentStatusChoices(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    PROCESSING = "PROCESSING", _("Processing")
    SUCCEEDED = "SUCCEEDED", _("Succeeded")
    FAILED = "FAILED", _("Failed")
    CANCELED = "CANCELED", _("Canceled")
    REFUNDED = "REFUNDED", _("Refunded")
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED", _("Partially Refunded")


class PaymentMethodChoices(models.TextChoices):
    CASH_ON_DELIVERY = "COD", _("Cash On Delivery")
    MOBILE_MONEY = "MOBILE_MONEY", _("Mobile Money")
    CREDIT_CARD = "CREDIT_CARD", _("Credit Card")
    DEBIT_CARD = "DEBIT_CARD", _("Debit Card")
    BANK_TRANSFER = "BANK_TRANSFER", _("Bank Transfer")
    PAYPAL = "PAYPAL", _("PayPal")


class PaymentProviderChoices(models.TextChoices):
    PAYUNIT = "PAYUNIT", _("PayUnit")
    STRIPE = "STRIPE", _("Stripe")
    MANUAL = "MANUAL", _("Manual")


class DeliveryStatusChoices(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    PICKED_UP = "PICKED_UP", _("Picked Up")
    IN_TRANSIT = "IN_TRANSIT", _("In Transit")
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY", _("Out For Delivery")
    DELIVERED = "DELIVERED", _("Delivered")
    RETURNED = "RETURNED", _("Returned")
    FAILED = "FAILED", _("Failed")


class DeliveryMethodChoices(models.TextChoices):
    STANDARD = "STANDARD", _("Standard Shipping")
    EXPRESS = "EXPRESS", _("Express Shipping")
    PICKUP = "PICKUP", _("In-Store Pickup")
    SAME_DAY = "SAME_DAY", _("Same Day Delivery")


class PromotionTypeChoices(models.TextChoices):
    PERCENTAGE = "PERCENTAGE", _("Percentage Discount")
    FIXED_AMOUNT = "FIXED_AMOUNT", _("Fixed Amount Discount")
    BUY_X_GET_Y = "BUY_X_GET_Y", _("Buy X Get Y")
    FREE_SHIPPING = "FREE_SHIPPING", _("Free Shipping")


class ArticleStatusChoices(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    PUBLISHED = "PUBLISHED", _("Published")
    ARCHIVED = "ARCHIVED", _("Archived")


class PriorityChoices(models.TextChoices):
    LOW = "LOW", _("Low")
    MEDIUM = "MEDIUM", _("Medium")
    HIGH = "HIGH", _("High")
    URGENT = "URGENT", _("Urgent")


class ReviewRatingChoices(models.IntegerChoices):
    ONE = 1, _("1 Star")
    TWO = 2, _("2 Stars")
    THREE = 3, _("3 Stars")
    FOUR = 4, _("4 Stars")
    FIVE = 5, _("5 Stars")
