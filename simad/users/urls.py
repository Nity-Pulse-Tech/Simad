from django.urls import path

from .views import (
    user_detail_view,
    user_redirect_view,
    user_update_view,
    LoginView,
    SignupView,
    VerifyCodeView,
    WhatsAppSentView,
    ActivateAccountView,
    ResendVerificationView,
)

app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<int:pk>/", view=user_detail_view, name="detail"),
    path("login/", view=LoginView.as_view(), name="login"),
    path("signup/", view=SignupView.as_view(), name="signup"),
    path("verify-code/", view=VerifyCodeView.as_view(), name="verify-code"),
    path("whatsapp-sent/", view=WhatsAppSentView.as_view(), name="whatsapp-sent"),
    path("activate/<str:token>/", view=ActivateAccountView.as_view(), name="activate-account"),
    path("resend-verification/", view=ResendVerificationView.as_view(), name="resend-verification"),
]
