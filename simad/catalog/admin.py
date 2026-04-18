from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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
    list_display = ["display_name", "parent", "is_featured", "status", "created"]
    list_filter = ["is_featured", "status"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["name"]

    @admin.display(description=_("Name"))
    def display_name(self, obj):
        if obj.parent:
            return f"{obj.parent.name} > {obj.name}"
        return obj.name


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name", "category", "price", "stock_status",
        "is_available", "is_featured", "status",
    ]
    list_filter = [
        "product_type", "is_available", "is_featured", "status", "category",
    ]
    search_fields = ["name", "sku", "barcode"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["-created"]
    readonly_fields = ["created", "modified"]
    autocomplete_fields = ["category"]
    inlines = [ProductImageInline, ProductVideoInline, ProductSpecificationInline]
    actions = ["make_available", "make_unavailable", "mark_as_featured"]
    
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
        ("Clinical & Usage", {
            "fields": ("clinical_notes", "usage_instructions", "precautions", "technical_details"),
        }),
        ("Related", {
            "fields": ("tags",),
        }),
        ("Timestamps", {
            "fields": ("created", "modified"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("Stock"))
    def stock_status(self, obj):
        if obj.stock_quantity <= 0:
            return mark_safe('<span style="color: red; font-weight: bold;">Out of Stock</span>')
        if obj.stock_quantity <= obj.low_stock_threshold:
            return mark_safe(f'<span style="color: orange; font-weight: bold;">Low Stock ({obj.stock_quantity})</span>')
        return f"{obj.stock_quantity} in stock"

    @admin.action(description=_("Mark selected products as available"))
    def make_available(self, request, queryset):
        queryset.update(is_available=True)

    @admin.action(description=_("Mark selected products as unavailable"))
    def make_unavailable(self, request, queryset):
        queryset.update(is_available=False)

    @admin.action(description=_("Mark selected products as featured"))
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)


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
    list_filter = ["promotion_type", "is_active", "start_date", "end_date"]
    search_fields = ["title", "code"]
    filter_horizontal = ["products", "categories"]
    readonly_fields = ["used_count", "created", "modified"]
    autocomplete_fields = ["products", "categories"]

    def save_model(self, request, obj, form, change):
        if obj.end_date and obj.start_date and obj.end_date < obj.start_date:
            from django.core.exceptions import ValidationError
            raise ValidationError(_("End date cannot be before start date."))
        super().save_model(request, obj, form, change)


@admin.register(FlashSale)
class FlashSaleAdmin(admin.ModelAdmin):
    list_display = [
        "product", "promotion", "sale_price", "sold_count",
        "stock_limit", "start_date", "end_date", "is_active",
    ]
    list_filter = ["start_date", "end_date"]
    search_fields = ["product__name", "promotion__title"]
    autocomplete_fields = ["product", "promotion"]

    @admin.display(boolean=True, description=_("Active"))
    def is_active(self, obj):
        now = timezone.now()
        return obj.start_date <= now <= obj.end_date


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
    readonly_fields = ["helpful_count", "not_helpful_count", "created", "modified", "admin_replied_at"]
    actions = ["approve_reviews", "reject_reviews", "mark_as_featured"]
    
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

    def save_model(self, request, obj, form, change):
        if change and 'admin_reply' in form.changed_data and obj.admin_reply:
            obj.admin_replied_at = timezone.now()
        super().save_model(request, obj, form, change)

    @admin.action(description=_("Approve selected reviews"))
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description=_("Reject selected reviews"))
    def reject_reviews(self, request, queryset):
        queryset.update(is_approved=False)

    @admin.action(description=_("Mark selected reviews as featured"))
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
