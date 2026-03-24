import logging

from django.http import JsonResponse
from django.views import View
from django.db.models import Q
from simad.catalog.models import Product

logger = logging.getLogger(__name__)

class ProductSearchView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()
        logger.info(
            "ProductSearchView GET — query='%s', user=%s, IP=%s",
            query,
            request.user if request.user.is_authenticated else "Anonymous",
            request.META.get("REMOTE_ADDR"),
        )

        if len(query) < 2:
            logger.debug("Query too short (%d chars), returning empty results", len(query))
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

        logger.info(
            "Search for '%s' returned %d results: %s",
            query,
            len(results),
            [r['name'] for r in results],
        )
        return JsonResponse({'results': results})
