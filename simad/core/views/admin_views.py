from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404
from django.utils.text import slugify

from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta

from simad.catalog.models import Product, Category, ProductImage, ProductVideo, Promotion, FlashSale
from simad.orders.models import Order, Delivery, Payment
from simad.users.models import User

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/admin_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Dashboard KPIs
        context['total_revenue'] = Order.objects.filter(is_paid=True).aggregate(Sum('total'))['total__sum'] or 0
        context['total_orders'] = Order.objects.count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        
        # Inventory Alerts
        context['low_stock_products'] = Product.objects.filter(
            stock_quantity__lte=models.F('low_stock_threshold'),
            stock_quantity__gt=0
        ).order_by('stock_quantity')[:5]
        context['out_of_stock_products'] = Product.objects.filter(stock_quantity=0)[:5]
        
        # Recent Activity Ledger (Last 10 Actions)
        # We'll use a simple approach: merge recent records from multiple models
        recent_orders = Order.objects.order_by('-created')[:5]
        recent_products = Product.objects.order_by('-created')[:5]
        recent_users = User.objects.order_by('-created')[:5]
        
        activity = []
        for o in recent_orders:
            activity.append({
                'description': f"Order {o.reference} placed",
                'category': 'Logistics',
                'executor': o.user.full_name if o.user else 'Guest',
                'timestamp': o.created,
                'status_color': 'primary'
            })
        for p in recent_products:
            activity.append({
                'description': f"New SKU: {p.name}",
                'category': 'Inventory',
                'executor': 'Admin',
                'timestamp': p.created,
                'status_color': 'tertiary'
            })
        for u in recent_users:
            activity.append({
                'description': f"User '{u.full_name or u.email}' joined",
                'category': 'Compliance',
                'executor': 'System',
                'timestamp': u.created,
                'status_color': 'amber-400'
            })
            
        activity.sort(key=lambda x: x['timestamp'], reverse=True)
        context['recent_activity'] = activity[:10]
        
        # Analytics (Last 7 Days)
        today = timezone.now().date()
        days = []
        revenue_data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            days.append(day.strftime('%b %d'))
            day_revenue = Order.objects.filter(
                created__date=day, 
                is_paid=True
            ).aggregate(Sum('total'))['total__sum'] or 0
            revenue_data.append(float(day_revenue))
            
        context['analytics_days'] = days
        context['analytics_revenue'] = revenue_data
        
        return context

class AdminPromotionsView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/promotion_and_flash_deal_managment.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        flash_sales = FlashSale.objects.all().order_by('-start_date')
        promotions = Promotion.objects.all().order_by('-start_date')
        context['flash_sales'] = flash_sales
        context['promotions'] = promotions
        context['active_flash_sales_count'] = flash_sales.filter(start_date__lte=timezone.now(), end_date__gte=timezone.now()).count()
        context['total_campaign_revenue'] = 248600 # Static for now
        return context

class AdminDeliveriesView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/delivry_management.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        deliveries = Delivery.objects.all().order_by('-created')
        context['deliveries'] = deliveries
        context['processing_count'] = deliveries.filter(status='PROCESSING').count()
        context['shipped_count'] = deliveries.filter(status='SHIPPED').count()
        context['delivered_today'] = deliveries.filter(status='DELIVERED', delivered_at__date=timezone.now().date()).count()
        return context

class AdminAddProductView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/add_product.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        data = request.POST
        files = request.FILES
        
        try:
            with transaction.atomic():
                name = data.get('name')
                slug = slugify(name)
                
                base_slug = slug
                counter = 1
                while Product.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                product = Product(
                    name=name,
                    slug=slug,
                    category_id=data.get('category') or None,
                    description=data.get('description', ''),
                    short_description=data.get('short_description', ''),
                    sku=data.get('sku', ''),
                    barcode=data.get('barcode', ''),
                    price=data.get('price') or 0,
                    cost_price=data.get('cost_price') or None,
                    stock_quantity=data.get('stock_quantity') or 0,
                    low_stock_threshold=data.get('low_stock_threshold') or 5,
                    weight=data.get('weight') or None,
                    is_featured=data.get('is_featured') == 'on',
                    is_available=data.get('is_available') == 'on',
                    clinical_notes=data.get('clinical_notes', ''),
                    precautions=data.get('precautions', ''),
                )

                if 'thumbnail' in files:
                    product.thumbnail = files['thumbnail']
                product.save()

                gallery_images = request.FILES.getlist('gallery_images')
                for idx, image in enumerate(gallery_images):
                    ProductImage.objects.create(
                        product=product,
                        image=image,
                        order=idx
                    )

                video_url = data.get('video_url')
                if video_url:
                    ProductVideo.objects.create(
                        product=product,
                        video_url=video_url,
                        title=f"{product.name} Video"
                    )

                messages.success(request, f"Product '{product.name}' created successfully!")
                return redirect('core:admin-product-list')
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"Failed to create product: {str(e)}")
            return self.get(request, *args, **kwargs)

class AdminProductListView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/product_management.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.all().order_by('-created')
        context['products'] = products
        
        # Stats Summary
        context['total_skus'] = products.count()
        context['out_of_stock_count'] = products.filter(stock_quantity=0).count()
        context['total_valuation'] = products.aggregate(Sum('price'))['price__sum'] or 0
        context['category_count'] = Category.objects.count()
        
        return context

class AdminDeleteProductView(AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, pk=pk)
        product_name = product.name
        product.delete()
        messages.success(request, f"Product '{product_name}' was successfully deleted.")
        return redirect('core:admin-product-list')

class AdminEditProductView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/add_product.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(Product, pk=self.kwargs['pk'])
        context['categories'] = Category.objects.all()
        return context

    def post(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, pk=pk)
        data = request.POST
        files = request.FILES
        
        try:
            with transaction.atomic():
                product.name = data.get('name')
                product.category_id = data.get('category') or None
                product.description = data.get('description', '')
                product.short_description = data.get('short_description', '')
                product.sku = data.get('sku', '')
                product.barcode = data.get('barcode', '')
                product.price = data.get('price') or 0
                product.cost_price = data.get('cost_price') or None
                product.stock_quantity = data.get('stock_quantity') or 0
                product.low_stock_threshold = data.get('low_stock_threshold') or 5
                product.weight = data.get('weight') or None
                product.is_featured = data.get('is_featured') == 'on'
                product.is_available = data.get('is_available') == 'on'
                product.clinical_notes = data.get('clinical_notes', '')
                product.precautions = data.get('precautions', '')

                if 'thumbnail' in files:
                    product.thumbnail = files['thumbnail']
                
                product.save()

                # Process new gallery images
                gallery_images = request.FILES.getlist('gallery_images')
                if gallery_images:
                    # Starting order from the current count
                    start_order = product.images.count()
                    for idx, image in enumerate(gallery_images):
                        ProductImage.objects.create(
                            product=product,
                            image=image,
                            order=start_order + idx
                        )

                video_url = data.get('video_url')
                if video_url:
                    pv, created = ProductVideo.objects.get_or_create(product=product, defaults={'title': f"{product.name} Video"})
                    pv.video_url = video_url
                    pv.save()

                messages.success(request, f"Product '{product.name}' was updated successfully!")
                return redirect('core:admin-product-list')
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"Failed to update product: {str(e)}")
            return self.get(request, *args, **kwargs)

class AdminUsersView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/user_management.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = User.objects.all().order_by('-created')
        context['users'] = users
        context['active_users'] = users.filter(is_active=True).count()
        return context

class AdminCorporateSettingsView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/corporate_settings.html"

class AdminLegalPagesView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/legal_pages_management.html"
