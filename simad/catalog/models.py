from django.db import models
from django.utils.translation import gettext_lazy as _

from simad.core.models import SIMADBASEMODEL
from simad.global_data.enum import ArticleStatusChoices
from simad.global_data.enum import ProductTypeChoices
from simad.global_data.enum import PromotionTypeChoices
from simad.global_data.enum import ReviewRatingChoices
from simad.global_data.enum import UnitOfMeasureChoices
from simad.users.models import User


# ──────────────────────────────────────────────
# Category
# ──────────────────────────────────────────────

class Category(SIMADBASEMODEL):
    name = models.CharField(_("Name"), max_length=150)
    slug = models.SlugField(_("Slug"), unique=True)
    description = models.TextField(_("Description"), blank=True)
    image = models.ImageField(
        _("Image"), upload_to="categories/", null=True, blank=True
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("Parent Category"),
    )
    is_featured = models.BooleanField(_("Featured"), default=False)

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name


# ──────────────────────────────────────────────
# Product
# ──────────────────────────────────────────────

class Product(SIMADBASEMODEL):
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name=_("Category"),
    )
    name = models.CharField(_("Name"), max_length=255)
    slug = models.SlugField(_("Slug"), unique=True)
    description = models.TextField(_("Description"), blank=True)
    short_description = models.CharField(
        _("Short Description"), max_length=500, blank=True
    )
    product_type = models.CharField(
        _("Product Type"),
        max_length=20,
        choices=ProductTypeChoices.choices,
        default=ProductTypeChoices.PHYSICAL,
    )
    sku = models.CharField(_("SKU"), max_length=100, unique=True, blank=True)
    barcode = models.CharField(_("Barcode"), max_length=100, blank=True)
    price = models.DecimalField(_("Price"), max_digits=12, decimal_places=2)
    compare_price = models.DecimalField(
        _("Compare At Price"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    cost_price = models.DecimalField(
        _("Cost Price"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    unit = models.CharField(
        _("Unit"),
        max_length=10,
        choices=UnitOfMeasureChoices.choices,
        default=UnitOfMeasureChoices.PIECE,
    )
    stock_quantity = models.PositiveIntegerField(_("Stock Quantity"), default=0)
    low_stock_threshold = models.PositiveIntegerField(
        _("Low Stock Threshold"), default=5
    )
    weight = models.DecimalField(
        _("Weight (kg)"), max_digits=8, decimal_places=2, null=True, blank=True
    )
    is_featured = models.BooleanField(_("Featured"), default=False)
    is_available = models.BooleanField(_("Available"), default=True)
    thumbnail = models.ImageField(
        _("Thumbnail"), upload_to="products/thumbnails/", null=True, blank=True
    )
    tags = models.ManyToManyField(
        "self", blank=True, symmetrical=False, related_name="related_products"
    )

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ["-created"]

    def __str__(self):
        return self.name

    @property
    def is_in_stock(self) -> bool:
        return self.stock_quantity > 0

    @property
    def discount_percentage(self) -> int | None:
        if self.compare_price and self.compare_price > self.price:
            return int(
                ((self.compare_price - self.price) / self.compare_price) * 100
            )
        return None


class ProductImage(SIMADBASEMODEL):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(_("Image"), upload_to="products/images/")
    alt_text = models.CharField(_("Alt Text"), max_length=255, blank=True)
    is_primary = models.BooleanField(_("Primary Image"), default=False)
    order = models.PositiveIntegerField(_("Display Order"), default=0)

    class Meta:
        verbose_name = _("Product Image")
        verbose_name_plural = _("Product Images")
        ordering = ["order"]

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductVideo(SIMADBASEMODEL):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="videos"
    )
    video = models.FileField(_("Video"), upload_to="products/videos/", null=True, blank=True)
    video_url = models.URLField(_("Video URL (YouTube/Vimeo)"), blank=True)
    title = models.CharField(_("Title"), max_length=255, blank=True)
    thumbnail = models.ImageField(
        _("Thumbnail"), upload_to="products/video_thumbs/", null=True, blank=True
    )
    duration_seconds = models.PositiveIntegerField(_("Duration (seconds)"), default=0)
    order = models.PositiveIntegerField(_("Display Order"), default=0)

    class Meta:
        verbose_name = _("Product Video")
        verbose_name_plural = _("Product Videos")
        ordering = ["order"]

    def __str__(self):
        return f"Video for {self.product.name}"


class ProductSpecification(SIMADBASEMODEL):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="specifications"
    )
    name = models.CharField(_("Attribute Name"), max_length=100)
    value = models.CharField(_("Attribute Value"), max_length=255)
    order = models.PositiveIntegerField(_("Display Order"), default=0)

    class Meta:
        verbose_name = _("Product Specification")
        verbose_name_plural = _("Product Specifications")
        ordering = ["order"]

    def __str__(self):
        return f"{self.name}: {self.value}"


# ──────────────────────────────────────────────
# Promotions
# ──────────────────────────────────────────────

class Promotion(SIMADBASEMODEL):
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    promotion_type = models.CharField(
        _("Promotion Type"),
        max_length=30,
        choices=PromotionTypeChoices.choices,
        default=PromotionTypeChoices.PERCENTAGE,
    )
    discount_value = models.DecimalField(
        _("Discount Value"), max_digits=10, decimal_places=2
    )
    code = models.CharField(_("Promo Code"), max_length=50, blank=True, unique=True)
    min_order_amount = models.DecimalField(
        _("Minimum Order Amount"), max_digits=12, decimal_places=2, default=0
    )
    max_uses = models.PositiveIntegerField(_("Maximum Uses"), null=True, blank=True)
    used_count = models.PositiveIntegerField(_("Times Used"), default=0)
    start_date = models.DateTimeField(_("Start Date"), null=True, blank=True)
    end_date = models.DateTimeField(_("End Date"), null=True, blank=True)
    products = models.ManyToManyField(
        Product, blank=True, related_name="promotions", verbose_name=_("Products")
    )
    categories = models.ManyToManyField(
        Category, blank=True, related_name="promotions", verbose_name=_("Categories")
    )
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Promotion")
        verbose_name_plural = _("Promotions")
        ordering = ["-created"]

    def __str__(self):
        return self.title


class FlashSale(SIMADBASEMODEL):
    promotion = models.ForeignKey(
        Promotion, on_delete=models.CASCADE, related_name="flash_sales"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="flash_sales"
    )
    sale_price = models.DecimalField(
        _("Sale Price"), max_digits=12, decimal_places=2
    )
    start_date = models.DateTimeField(_("Start Date"))
    end_date = models.DateTimeField(_("End Date"))
    stock_limit = models.PositiveIntegerField(
        _("Stock Limit for Flash Sale"), null=True, blank=True
    )
    sold_count = models.PositiveIntegerField(_("Sold Count"), default=0)
    banner_image = models.ImageField(
        _("Banner Image"), upload_to="flash_sales/", null=True, blank=True
    )

    class Meta:
        verbose_name = _("Flash Sale")
        verbose_name_plural = _("Flash Sales")
        ordering = ["-start_date"]

    def __str__(self):
        return f"Flash Sale: {self.product.name}"


# ──────────────────────────────────────────────
# Content
# ──────────────────────────────────────────────

class ArticleCategory(SIMADBASEMODEL):
    name = models.CharField(_("Name"), max_length=150)
    slug = models.SlugField(_("Slug"), unique=True)
    description = models.TextField(_("Description"), blank=True)

    class Meta:
        verbose_name = _("Article Category")
        verbose_name_plural = _("Article Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Article(SIMADBASEMODEL):
    category = models.ForeignKey(
        ArticleCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )
    title = models.CharField(_("Title"), max_length=255)
    slug = models.SlugField(_("Slug"), unique=True)
    summary = models.CharField(_("Summary"), max_length=500, blank=True)
    content = models.TextField(_("Content"))
    cover_image = models.ImageField(
        _("Cover Image"), upload_to="articles/", null=True, blank=True
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ArticleStatusChoices.choices,
        default=ArticleStatusChoices.DRAFT,
    )
    is_featured = models.BooleanField(_("Featured"), default=False)
    published_at = models.DateTimeField(_("Published At"), null=True, blank=True)
    read_time_minutes = models.PositiveIntegerField(
        _("Estimated Read Time (minutes)"), default=0
    )
    views_count = models.PositiveIntegerField(_("Views Count"), default=0)

    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")
        ordering = ["-published_at"]

    def __str__(self):
        return self.title


class Testimonial(SIMADBASEMODEL):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="testimonials",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="testimonials",
    )
    full_name = models.CharField(_("Full Name"), max_length=150)
    content = models.TextField(_("Testimonial Content"))
    rating = models.IntegerField(
        _("Rating"),
        choices=ReviewRatingChoices.choices,
        default=ReviewRatingChoices.FIVE,
    )
    avatar = models.ImageField(
        _("Avatar"), upload_to="testimonials/", null=True, blank=True
    )
    is_published = models.BooleanField(_("Published"), default=False)

    class Meta:
        verbose_name = _("Testimonial")
        verbose_name_plural = _("Testimonials")
        ordering = ["-created"]

    def __str__(self):
        return f"{self.full_name} – {self.rating}★"


# ──────────────────────────────────────────────
# Product Reviews (by verified buyers / clients)
# ──────────────────────────────────────────────

class ProductReview(SIMADBASEMODEL):
    """
    A review left by a customer on a product they purchased.
    Can be verified against their order history.
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
    )
    # For anonymous / guest reviewers
    reviewer_name = models.CharField(_("Reviewer Name"), max_length=150, blank=True)
    reviewer_email = models.EmailField(_("Reviewer Email"), blank=True)

    rating = models.IntegerField(
        _("Rating"),
        choices=ReviewRatingChoices.choices,
        default=ReviewRatingChoices.FIVE,
    )
    title = models.CharField(_("Review Title"), max_length=255, blank=True)
    body = models.TextField(_("Review Body"))

    # Verify the reviewer actually purchased the product
    is_verified_purchase = models.BooleanField(_("Verified Purchase"), default=False)

    # Admin moderation
    is_approved = models.BooleanField(_("Approved"), default=False)
    is_featured = models.BooleanField(_("Featured Review"), default=False)

    # Helpfulness votes (other users found this review helpful)
    helpful_count = models.PositiveIntegerField(_("Helpful Votes"), default=0)
    not_helpful_count = models.PositiveIntegerField(_("Not Helpful Votes"), default=0)

    # Admin reply / vendor response
    admin_reply = models.TextField(_("Admin Reply"), blank=True)
    admin_replied_at = models.DateTimeField(_("Admin Replied At"), null=True, blank=True)

    class Meta:
        verbose_name = _("Product Review")
        verbose_name_plural = _("Product Reviews")
        ordering = ["-created"]
        # One review per user per product (for logged-in users)
        constraints = [
            models.UniqueConstraint(
                fields=["product", "user"],
                condition=models.Q(user__isnull=False),
                name="unique_review_per_user_per_product",
            )
        ]

    def __str__(self):
        reviewer = self.reviewer_name or (str(self.user) if self.user else "Anonymous")
        return f"{reviewer} – {self.rating}★ on {self.product.name}"

