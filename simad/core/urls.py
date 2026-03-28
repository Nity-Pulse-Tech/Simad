from django.urls import path
from .views import (
    HomeView,
    ProductListView,
    ProductDetailView,
    CartView,
    OrderSummaryView,
    PaymentView,
    PaymentSuccessView,
    PaymentFailureView,
    CreateOrderView,
    WishlistToggleView,
    ProductSearchView,
    SolutionsView,
    PromotionsView,
    AboutUsView,
    AdminDashboardView,
    AdminDeliveriesView,
    AdminPromotionsView,
    AdminAddProductView,
    AdminProductListView,
    AdminUsersView,
)

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("solutions/", SolutionsView.as_view(), name="solutions"),
    path("promotions/", PromotionsView.as_view(), name="promotions"),
    path("about-us/", AboutUsView.as_view(), name="about-us"),
    path("wishlist/toggle/", WishlistToggleView.as_view(), name="wishlist-toggle"),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<slug:slug>/", ProductDetailView.as_view(), name="product-detail"),
    path("checkout/cart/", CartView.as_view(), name="cart"),
    path("checkout/order/create/", CreateOrderView.as_view(), name="order-create"),
    path("checkout/summary/", OrderSummaryView.as_view(), name="order-summary"),
    path("checkout/payment/", PaymentView.as_view(), name="payment"),
    path("checkout/success/", PaymentSuccessView.as_view(), name="payment-success"),
    path("checkout/failure/", PaymentFailureView.as_view(), name="payment-failure"),
    path("api/search/", ProductSearchView.as_view(), name="api-search"),
    
    # Admin URLs
    path("admin-dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("admin-dashboard/deliveries/", AdminDeliveriesView.as_view(), name="admin-deliveries"),
    path("admin-dashboard/promotions/", AdminPromotionsView.as_view(), name="admin-promotions"),
    path("admin-dashboard/add-product/", AdminAddProductView.as_view(), name="admin-add-product"),
    path("admin-dashboard/products/", AdminProductListView.as_view(), name="admin-product-list"),
    path("admin-dashboard/users/", AdminUsersView.as_view(), name="admin-users"),
]
