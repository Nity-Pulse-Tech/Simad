from django.views.generic import ListView, DetailView
from simad.catalog.models import Product, Category, ProductSpecification

class ProductListView(ListView):
    model = Product
    template_name = "pages/product/product.html"
    context_object_name = "products"
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Categories for "Type de Produit"
        context["categories"] = Category.objects.all()
        
        # Unique specification values for filters
        context["contenance_options"] = ProductSpecification.objects.filter(
            name='Contenance'
        ).values_list('value', flat=True).distinct().order_by('value')
        
        context["application_options"] = ProductSpecification.objects.filter(
            name='Application'
        ).values_list('value', flat=True).distinct().order_by('value')
        
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = "pages/product/detail.html"
    context_object_name = "product"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        # Images are accessible via product.images.all() in template thanks to related_name
        # Reviews are accessible via product.reviews.all()
        
        # Fetch related products (same category, excluding current product)
        context["related_products"] = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:3]
        
        return context
