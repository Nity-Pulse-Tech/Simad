from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404
from django.utils.text import slugify

from simad.catalog.models import Product, Category, ProductImage, ProductVideo

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/admin_dashboard.html"

class AdminDeliveriesView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/delivry_management.html"

class AdminPromotionsView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/promotion_and_flash_deal_managment.html"

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
        context['products'] = Product.objects.all().order_by('-created')
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

class AdminCorporateSettingsView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/corporate_settings.html"

class AdminLegalPagesView(AdminRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/legal_pages_management.html"
