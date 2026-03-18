from django.views.generic import TemplateView
from simad.catalog.models import Product, Wishlist

class HomeView(TemplateView):
    template_name = "pages/home/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch 8 products for the home page grid
        context["products"] = Product.objects.all()[:8]
        
        # Add wishlist product IDs if user is authenticated
        if self.request.user.is_authenticated:
            context["wishlist_product_ids"] = list(
                Wishlist.objects.filter(user=self.request.user).values_list('product_id', flat=True)
            )
        else:
            context["wishlist_product_ids"] = []
            
        return context
