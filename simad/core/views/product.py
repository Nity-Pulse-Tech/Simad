import json
import datetime
import logging
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
from simad.orders.tasks import send_order_notifications

logger = logging.getLogger(__name__)

class WishlistToggleView(View):
    def post(self, request, *args, **kwargs):
        logger.info(
            "WishlistToggleView POST — user=%s, IP=%s",
            request.user if request.user.is_authenticated else "Anonymous",
            request.META.get("REMOTE_ADDR"),
        )

        if not request.user.is_authenticated:
            logger.warning("Unauthenticated user tried to toggle wishlist")
            return JsonResponse({
                'success': False,
                'status': 'error',
                'message': "Tu dois être connecté avant d'ajouter aux favoris"
            }, status=401)

        product_id = request.POST.get('product_id')
        logger.info("Wishlist toggle for product_id=%s by user=%s", product_id, request.user.email)
        product = get_object_or_404(Product, id=product_id)

        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )

        if not created:
            wishlist_item.delete()
            logger.info(
                "Product '%s' (id=%s) REMOVED from wishlist for user %s",
                product.name,
                product_id,
                request.user.email,
            )
            return JsonResponse({
                'success': True,
                'status': 'removed',
                'message': 'Produit retiré des favoris.'
            })

        logger.info(
            "Product '%s' (id=%s) ADDED to wishlist for user %s",
            product.name,
            product_id,
            request.user.email,
        )
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

    def get(self, request, *args, **kwargs):
        logger.info(
            "ProductListView GET — user=%s, IP=%s, params=%s",
            request.user if request.user.is_authenticated else "Anonymous",
            request.META.get("REMOTE_ADDR"),
            dict(request.GET),
        )
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        logger.info("ProductListView.get_queryset() called")
        queryset = super().get_queryset()

        # Search query
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q) |
                Q(short_description__icontains=q)
            )
            logger.info("Applied search filter: q='%s'", q)

        # Category filter
        categories = self.request.GET.getlist('category')
        if categories:
            queryset = queryset.filter(category__name__in=categories)
            logger.info("Applied category filter: %s", categories)

        # Contenance filter (Specification)
        contenance = self.request.GET.getlist('contenance')
        if contenance:
            product_ids = ProductSpecification.objects.filter(
                name='Contenance',
                value__in=contenance
            ).values_list('product_id', flat=True)
            queryset = queryset.filter(id__in=product_ids)
            logger.info("Applied contenance filter: %s → %d product IDs", contenance, len(product_ids))

        # Application filter (Specification)
        application = self.request.GET.getlist('application')
        if application:
            product_ids = ProductSpecification.objects.filter(
                name='Application',
                value__in=application
            ).values_list('product_id', flat=True)
            queryset = queryset.filter(id__in=product_ids)
            logger.info("Applied application filter: %s → %d product IDs", application, len(product_ids))

        # Price range
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
            logger.info("Applied min_price filter: %s", min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
            logger.info("Applied max_price filter: %s", max_price)

        final_qs = queryset.distinct()
        logger.info("ProductListView queryset final count: %d", final_qs.count())
        return final_qs

    def get_context_data(self, **kwargs):
        logger.info("ProductListView.get_context_data() called")
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
        logger.debug("Current filters: %s", context["current_filters"])

        # Add wishlist product IDs if user is authenticated
        if self.request.user.is_authenticated:
            wishlist_ids = list(
                Wishlist.objects.filter(user=self.request.user).values_list('product_id', flat=True)
            )
            context["wishlist_product_ids"] = wishlist_ids
            logger.info("User %s has %d wishlist items", self.request.user.email, len(wishlist_ids))
        else:
            context["wishlist_product_ids"] = []

        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = "pages/product/detail.html"
    context_object_name = "product"
    slug_url_kwarg = "slug"

    def get(self, request, *args, **kwargs):
        logger.info(
            "ProductDetailView GET — slug=%s, user=%s, IP=%s",
            kwargs.get("slug"),
            request.user if request.user.is_authenticated else "Anonymous",
            request.META.get("REMOTE_ADDR"),
        )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        logger.info(
            "ProductDetailView — product='%s' (id=%s, slug=%s, price=%s)",
            product.name,
            product.id,
            product.slug,
            product.price,
        )

        # Fetch related products (same category, excluding current product)
        related = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:3]
        context["related_products"] = related
        logger.info("Found %d related products for category '%s'", len(related), product.category)

        # Check if current product is in wishlist
        if self.request.user.is_authenticated:
            is_in_wishlist = Wishlist.objects.filter(
                user=self.request.user, product=product
            ).exists()
            context["is_in_wishlist"] = is_in_wishlist
            context["wishlist_product_ids"] = list(
                Wishlist.objects.filter(user=self.request.user).values_list('product_id', flat=True)
            )
            logger.info(
                "User %s — product '%s' in wishlist: %s",
                self.request.user.email,
                product.name,
                is_in_wishlist,
            )
        else:
            context["is_in_wishlist"] = False
            context["wishlist_product_ids"] = []
            logger.debug("Anonymous user viewing product '%s'", product.name)

        return context

def generate_order_reference():
    date_part = datetime.datetime.now().strftime('%Y%m%d')
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    ref = f"SIM-{date_part}-{random_part}"
    logger.debug("Generated order reference: %s", ref)
    return ref

@method_decorator(csrf_exempt, name='dispatch')
class CreateOrderView(View):
    def post(self, request, *args, **kwargs):
        logger.info(
            "CreateOrderView POST — user=%s, IP=%s, content_type=%s",
            request.user if request.user.is_authenticated else "Anonymous",
            request.META.get("REMOTE_ADDR"),
            request.content_type,
        )

        if not request.user.is_authenticated:
            logger.warning("Unauthenticated user attempted to create order")
            return JsonResponse({
                'success': False,
                'error': 'login_required',
                'message': 'Vous devez être connecté pour passer une commande.'
            }, status=401)

        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            logger.info(
                "CreateOrderView — user=%s, items count=%d, raw items=%s",
                request.user.email,
                len(items),
                items,
            )

            if not items:
                logger.warning("CreateOrderView — empty cart for user %s", request.user.email)
                return JsonResponse({'success': False, 'error': 'Le panier est vide.'}, status=400)

            # Create the order
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                reference=generate_order_reference(),
                subtotal=0,
                total=0,
                shipping_cost=1500,  # Fixed as per request
            )
            logger.info(
                "Order created — reference=%s, order_id=%s, user=%s",
                order.reference,
                order.id,
                request.user.email,
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
                    line_total = price * qty
                    total_subtotal += line_total
                    logger.info(
                        "OrderItem added — product='%s' (id=%s), qty=%d, unit_price=%s, line_total=%s",
                        product.name,
                        product.id,
                        qty,
                        price,
                        line_total,
                    )
                except Product.DoesNotExist:
                    logger.error("Product with id=%s does not exist — skipping item", item.get('id'))
                    continue

            order.subtotal = total_subtotal
            order.total = total_subtotal + 1500  # Subtotal + Delivery
            order.save()
            logger.info(
                "Order finalized — reference=%s, subtotal=%s, shipping=1500, total=%s",
                order.reference,
                order.subtotal,
                order.total,
            )

            # Trigger asynchronous notifications
            send_order_notifications.delay(order.id)
            logger.info("Order notifications dispatched for order %s (id=%s)", order.reference, order.id)

            # Store reference in session for the summary page
            request.session['order_ref'] = order.reference
            request.session.modified = True
            logger.info(
                "Stored order_ref='%s' in session (session_key=%s)",
                order.reference,
                request.session.session_key,
            )

            return JsonResponse({
                'success': True,
                'reference': order.reference,
                'order_id': str(order.id)
            })

        except json.JSONDecodeError as e:
            logger.error("CreateOrderView — invalid JSON body: %s", e)
            return JsonResponse({'success': False, 'error': 'Invalid request body.'}, status=400)
        except Exception as e:
            logger.exception("CreateOrderView — unexpected error for user %s: %s", request.user.email, e)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
