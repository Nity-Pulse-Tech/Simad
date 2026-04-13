import logging

from django.views.generic import TemplateView
from simad.catalog.models import Product, Wishlist, Article, Testimonial

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = "pages/home/home.html"

    def get_context_data(self, **kwargs):
        logger.info("HomeView.get_context_data() called")
        context = super().get_context_data(**kwargs)

        try:
            # Evaluate queryset immediately so logging and template rendering are predictable
            # Prioritize featured products, then latest products
            products = list(Product.objects.filter(is_available=True).order_by('-is_featured', '-created')[:8])
            context["products"] = products
            logger.info("Fetched %d products for home page grid (featured first)", len(products))
        except Exception:
            logger.exception("Failed to load products for home page")
            context["products"] = []

        try:
            # Fetch latest 3 published articles
            articles = list(Article.objects.filter(status="PUBLISHED").select_related('category', 'author')[:3])
            context["articles"] = articles
            logger.info("Fetched %d articles for home page", len(articles))
        except Exception:
            logger.exception("Failed to load articles for home page")
            context["articles"] = []

        try:
            # Fetch latest 3 published testimonials
            testimonials = list(Testimonial.objects.filter(is_published=True).select_related('user', 'product')[:3])
            context["testimonials"] = testimonials
            logger.info("Fetched %d testimonials for home page", len(testimonials))
        except Exception:
            logger.exception("Failed to load testimonials for home page")
            context["testimonials"] = []

        try:
            if self.request.user.is_authenticated:
                wishlist_ids = list(
                    Wishlist.objects.filter(user=self.request.user)
                    .values_list("product_id", flat=True)
                )
                context["wishlist_product_ids"] = wishlist_ids
                logger.info(
                    "User %s is authenticated — loaded %d wishlist items",
                    self.request.user.email,
                    len(wishlist_ids),
                )
            else:
                context["wishlist_product_ids"] = []
                logger.info("Anonymous user — no wishlist loaded")
        except Exception:
            logger.exception("Failed to load wishlist for home page")
            context["wishlist_product_ids"] = []

        logger.debug("HomeView context keys: %s", list(context.keys()))
        return context

    def get(self, request, *args, **kwargs):
        logger.info(
            "HomeView GET request from %s (IP: %s)",
            request.user if request.user.is_authenticated else "Anonymous",
            request.META.get("REMOTE_ADDR"),
        )
        return super().get(request, *args, **kwargs)
class SolutionsView(TemplateView):
    template_name = "pages/home/solutions.html"


class PromotionsView(TemplateView):
    template_name = "pages/home/promotions.html"


class AboutUsView(TemplateView):
    template_name = "pages/home/about-us.html"


class ContactView(TemplateView):
    template_name = "pages/home/contact.html"

