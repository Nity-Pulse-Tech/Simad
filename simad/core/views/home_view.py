from django.views.generic import TemplateView
from simad.catalog.models import Product

class HomeView(TemplateView):
    template_name = "pages/home/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch 8 products for the home page grid
        context["products"] = Product.objects.all()[:8]
        return context
