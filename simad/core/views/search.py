from django.http import JsonResponse
from django.views import View
from django.db.models import Q
from simad.catalog.models import Product

class ProductSearchView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return JsonResponse({'results': []})

        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query)
        ).distinct()[:5]

        results = []
        for product in products:
            results.append({
                'id': str(product.id),
                'name': product.name,
                'slug': product.slug,
                'price': float(product.price),
                'thumbnail': product.thumbnail.url if product.thumbnail else None,
                'url': f"/products/{product.slug}/",
            })

        return JsonResponse({'results': results})
