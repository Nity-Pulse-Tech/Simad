from django.views.generic import TemplateView

class ProductListView(TemplateView):
    template_name = "pages/product/product.html"

class ProductDetailView(TemplateView):
    template_name = "pages/product/detail.html"
