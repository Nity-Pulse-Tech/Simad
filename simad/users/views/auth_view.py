from django.views.generic import TemplateView

class LoginView(TemplateView):
    template_name = "pages/auth/login.html"

class SignupView(TemplateView):
    template_name = "pages/auth/sigup.html"
