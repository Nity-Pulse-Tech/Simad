import json
import datetime
import random
import string
from django.http import JsonResponse
from django.db.models import Q
from django.views import View
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from simad.catalog.models import Product, Category, ProductSpecification, Wishlist
from simad.orders.models import Order, OrderItem

class WishlistToggleView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user, 
            product=product
        )
        
        if not created:
            wishlist_item.delete()
            return JsonResponse({
                'success': True,
                'status': 'removed', 
                'message': 'Produit retiré des favoris.'
            })
            
        return JsonResponse({
            'success': True,
            'status': 'added', 
            'message': 'Produit ajouté aux favoris.'
        })

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
        
        # Add wishlist product IDs if user is authenticated
        if self.request.user.is_authenticated:
            context["wishlist_product_ids"] = list(
                Wishlist.objects.filter(user=self.request.user).values_list('product_id', flat=True)
            )
        else:
            context["wishlist_product_ids"] = []
            
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
        
        # Check if current product is in wishlist
        if self.request.user.is_authenticated:
            context["is_in_wishlist"] = Wishlist.objects.filter(
                user=self.request.user, product=product
            ).exists()
            context["wishlist_product_ids"] = list(
                Wishlist.objects.filter(user=self.request.user).values_list('product_id', flat=True)
            )
        else:
            context["is_in_wishlist"] = False
            context["wishlist_product_ids"] = []
            
        return context

def generate_order_reference():
    date_part = datetime.datetime.now().strftime('%Y%m%d')
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"SIM-{date_part}-{random_part}"

@method_decorator(csrf_exempt, name='dispatch')
class CreateOrderView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False, 
                'error': 'login_required',
                'message': 'Vous devez être connecté pour passer une commande.'
            }, status=401)
            
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            
            if not items:
                return JsonResponse({'success': False, 'error': 'Le panier est vide.'}, status=400)

            # Create the order
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                reference=generate_order_reference(),
                subtotal=0,
                total=0,
                shipping_cost=1500, # Fixed as per request
            )

            total_subtotal = 0
            for item in items:
                # Get the product to ensure price and name are correct
                try:
                    product = Product.objects.get(id=item['id'])
                    qty = int(item['quantity'])
                    price = float(product.price)
                    
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        quantity=qty,
                        unit_price=price
                    )
                    total_subtotal += (price * qty)
                except Product.DoesNotExist:
                    continue

            order.subtotal = total_subtotal
            order.total = total_subtotal + 1500 # Subtotal + Delivery
            order.save()

            # Store reference in session for the summary page
            request.session['order_ref'] = order.reference
            request.session.modified = True
            print(f"DEBUG: Stored order_ref in session: {order.reference}")
            print(f"DEBUG: Session ID in CreateOrderView: {request.session.session_key}")

            return JsonResponse({
                'success': True,
                'reference': order.reference,
                'order_id': str(order.id)
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
