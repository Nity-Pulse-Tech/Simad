from django.contrib import admin

from .models import Article
from .models import ArticleCategory
from .models import Category
from .models import FlashSale
from .models import Product
from .models import ProductImage
from .models import ProductReview
from .models import ProductSpecification
from .models import ProductVideo
from .models import Promotion
from .models import Testimonial


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ["image", "alt_text", "is_primary", "order"]


class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 0
    fields = ["video", "video_url", "title", "order"]


class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1
    fields = ["name", "value", "order"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "is_featured", "status", "created"]
    list_filter = ["is_featured", "status"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name", "category", "product_type", "price", "stock_quantity",
        "is_available", "is_featured", "status", "created",
    ]
    list_filter = ["product_type", "is_available", "is_featured", "status", "category"]
    search_fields = ["name", "sku", "barcode"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["-created"]
    readonly_fields = ["created", "modified"]
    inlines = [ProductImageInline, ProductVideoInline, ProductSpecificationInline]
    fieldsets = (
        ("Basic Information", {
            "fields": ("category", "name", "slug", "product_type", "short_description", "description", "thumbnail"),
        }),
        ("Pricing", {
            "fields": ("price", "compare_price", "cost_price"),
        }),
        ("Inventory", {
            "fields": ("sku", "barcode", "unit", "stock_quantity", "low_stock_threshold", "weight"),
        }),
        ("Visibility", {
            "fields": ("is_available", "is_featured", "status"),
        }),
        ("Timestamps", {
            "fields": ("created", "modified"),
            "classes": ("collapse",),
        }),
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ["product", "is_primary", "order", "created"]
    list_filter = ["is_primary"]
    search_fields = ["product__name", "alt_text"]


@admin.register(ProductVideo)
class ProductVideoAdmin(admin.ModelAdmin):
    list_display = ["product", "title", "order", "created"]
    search_fields = ["product__name", "title"]


@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ["product", "name", "value", "order"]
    search_fields = ["product__name", "name", "value"]


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = [
        "title", "promotion_type", "discount_value", "code",
        "used_count", "max_uses", "is_active", "start_date", "end_date",
    ]
    list_filter = ["promotion_type", "is_active"]
    search_fields = ["title", "code"]
    filter_horizontal = ["products", "categories"]
    readonly_fields = ["used_count", "created", "modified"]


@admin.register(FlashSale)
class FlashSaleAdmin(admin.ModelAdmin):
    list_display = [
        "product", "promotion", "sale_price", "sold_count",
        "stock_limit", "start_date", "end_date",
    ]
    list_filter = ["start_date", "end_date"]
    search_fields = ["product__name"]


@admin.register(ArticleCategory)
class ArticleCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = [
        "title", "category", "author", "status", "is_featured",
        "published_at", "views_count",
    ]
    list_filter = ["status", "is_featured", "category"]
    search_fields = ["title", "summary"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["views_count", "created", "modified"]
    fieldsets = (
        ("Content", {
            "fields": ("category", "author", "title", "slug", "summary", "content", "cover_image"),
        }),
        ("Settings", {
            "fields": ("status", "is_featured", "published_at", "read_time_minutes"),
        }),
        ("Stats", {
            "fields": ("views_count", "created", "modified"),
            "classes": ("collapse",),
        }),
    )


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ["full_name", "product", "rating", "is_published", "created"]
    list_filter = ["rating", "is_published"]
    search_fields = ["full_name", "content"]
    readonly_fields = ["created", "modified"]


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = [
        "__str__", "product", "rating", "is_verified_purchase",
        "is_approved", "is_featured", "helpful_count", "created",
    ]
    list_filter = ["rating", "is_verified_purchase", "is_approved", "is_featured"]
    search_fields = ["product__name", "reviewer_name", "reviewer_email", "title", "body"]
    readonly_fields = ["helpful_count", "not_helpful_count", "created", "modified"]
    fieldsets = (
        ("Reviewer", {
            "fields": ("product", "user", "reviewer_name", "reviewer_email"),
        }),
        ("Review Content", {
            "fields": ("rating", "title", "body"),
        }),
        ("Moderation", {
            "fields": ("is_verified_purchase", "is_approved", "is_featured"),
        }),
        ("Admin Reply", {
            "fields": ("admin_reply", "admin_replied_at"),
        }),
        ("Votes", {
            "fields": ("helpful_count", "not_helpful_count"),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created", "modified"),
            "classes": ("collapse",),
        }),
    )
