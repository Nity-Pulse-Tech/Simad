from django.urls import path

from .views import (
    LoginView,
    SignupView,
    VerifyCodeView,
    WhatsAppSentView,
    ActivateAccountView,
    ResendVerificationView,
    LogoutView,
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
]
