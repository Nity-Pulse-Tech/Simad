from django.db.models import Q
from django.views.generic import ListView, DetailView
from simad.catalog.models import Product, Category, ProductSpecification

class ProductListView(ListView):
    model = Product
    template_name = "pages/product/product.html"
    context_object_name = "products"
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search query
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | 
                Q(description__icontains=q) | 
                Q(short_description__icontains=q)
            )

        # Category filter
        categories = self.request.GET.getlist('category')
        if categories:
            queryset = queryset.filter(category__name__in=categories)

        # Contenance filter (Specification)
        contenance = self.request.GET.getlist('contenance')
        if contenance:
            product_ids = ProductSpecification.objects.filter(
                name='Contenance', 
                value__in=contenance
            ).values_list('product_id', flat=True)
            queryset = queryset.filter(id__in=product_ids)

        # Application filter (Specification)
        application = self.request.GET.getlist('application')
        if application:
            product_ids = ProductSpecification.objects.filter(
                name='Application', 
                value__in=application
            ).values_list('product_id', flat=True)
            queryset = queryset.filter(id__in=product_ids)

        # Price range
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset.distinct()

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
        
        # Current filter states for the UI
        context["current_filters"] = {
            "q": self.request.GET.get("q", ""),
            "categories": self.request.GET.getlist("category"),
            "contenance": self.request.GET.getlist("contenance"),
            "application": self.request.GET.getlist("application"),
            "min_price": self.request.GET.get("min_price", ""),
            "max_price": self.request.GET.get("max_price", ""),
        }
        
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
