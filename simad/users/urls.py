from django.urls import path

from .views import (
    LoginView,
    SignupView,
    VerifyCodeView,
    WhatsAppSentView,
    ActivateAccountView,
    ResendVerificationView,
    LogoutView,
    UserDashboardView,
    MyOrderView,
    MyInvoiceView,
    AddressView,
    ProfileView,
    OrderDetailView,
    FavoritesView,
    MyQRCodesView,
)

app_name = "users"
urlpatterns = [
    path("login/", view=LoginView.as_view(), name="login"),
    path("signup/", view=SignupView.as_view(), name="signup"),
    path("verify-code/", view=VerifyCodeView.as_view(), name="verify-code"),
    path("whatsapp-sent/", view=WhatsAppSentView.as_view(), name="whatsapp-sent"),
    path("activate/<str:token>/", view=ActivateAccountView.as_view(), name="activate-account"),
    path("resend-verification/", view=ResendVerificationView.as_view(), name="resend-verification"),
    path("logout/", view=LogoutView.as_view(), name="logout"),
    path("dashboard/", view=UserDashboardView.as_view(), name="dashboard"),
    path("dashboard/favorites/", view=FavoritesView.as_view(), name="favorites"),
    path("dashboard/orders/", view=MyOrderView.as_view(), name="my-orders"),
    path("dashboard/invoices/", view=MyInvoiceView.as_view(), name="my-invoices"),
    path("dashboard/addresses/", view=AddressView.as_view(), name="addresses"),
    path("dashboard/profile/", view=ProfileView.as_view(), name="profile"),
    path("dashboard/qr-codes/", view=MyQRCodesView.as_view(), name="my-qr-codes"),
    path("dashboard/orders/<uuid:pk>/", view=OrderDetailView.as_view(), name="order-detail"),
]
