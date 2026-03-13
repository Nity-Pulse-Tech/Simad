import random
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.shortcuts import redirect
from django.views.generic import TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.contrib import messages
from ..models import User

class LoginView(TemplateView):
    template_name = "pages/auth/login.html"

class SignupView(TemplateView):
    template_name = "pages/auth/signup.html"

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        full_name = request.POST.get('full_name')
        phone_number = request.POST.get('phone_number')
        terms_accepted = request.POST.get('terms_accepted') == 'on'
        verification_method = request.POST.get('verification', 'email')
        
        if not email:
            messages.error(request, "Email is required.")
            return self.get(request, *args, **kwargs)

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return self.get(request, *args, **kwargs)

        if not terms_accepted:
            messages.error(request, "You must accept the Terms of Service.")
            return self.get(request, *args, **kwargs)

        # Simple user creation for now, assuming form validation is handled or will be
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return self.get(request, *args, **kwargs)
            
        from django.utils import timezone
        user = User.objects.create_user(
            email=email,
            password=password,
            phone_number=phone_number,
            is_active=False, # Keep inactive until verified
            terms_accepted=True,
            terms_accepted_at=timezone.now()
        )
        
        # Split Full Name if possible
        if full_name:
            names = full_name.split(' ', 1)
            user.first_name = names[0]
            if len(names) > 1:
                user.last_name = names[1]
            user.save()

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        
        # Store in cache for 10 minutes
        cache_key = f"otp_verification_{email}"
        cache.set(cache_key, otp, timeout=600)
        
        # Determine where to send (for now emailing as requested, but logic is ready for WhatsApp)
        if verification_method == 'email':
            # Send Email
            context = {'otp_code': otp, 'user': user}
            html_message = render_to_string('email/otp_email.html', context)
            send_mail(
                subject="Your Verification Code - SIMAD",
                message=f"Your verification code is {otp}",
                from_email=None,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
        elif verification_method == 'whatsapp':
            # Placeholder for WhatsApp logic
            # For now, still send email as fallback or per user request "so for now user email please"
            context = {'otp_code': otp, 'user': user}
            html_message = render_to_string('email/otp_email.html', context)
            send_mail(
                subject="Your Verification Code - SIMAD",
                message=f"Your verification code is {otp}",
                from_email=None,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            messages.info(request, "OTP sent to your email (WhatsApp integration coming soon).")
        
        # Store email in session to know who we are verifying
        request.session['verification_email'] = email
        
        messages.success(request, f"Account created! A verification code has been sent to {email}.")
        return redirect('users:verify-code')

class VerifyCodeView(TemplateView):
    template_name = "pages/auth/verify_code.html"

    def post(self, request, *args, **kwargs):
        email = request.session.get('verification_email')
        if not email:
            return redirect('users:signup')
            
        entered_code = request.POST.get('code') # Assuming Alpine.js submits a single field 'code'
        cache_key = f"otp_verification_{email}"
        stored_otp = cache.get(cache_key)
        
        if stored_otp and entered_code == stored_otp:
            # Success
            user = User.objects.get(email=email)
            user.is_active = True
            user.is_email_verified = True
            user.save()
            
            # Log the user in
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # Cleanup cache
            cache.delete(cache_key)
            del request.session['verification_email']
            
            messages.success(request, "Account verified successfully!")
            return redirect('users:redirect')
        else:
            messages.error(request, "Invalid or expired code.")
            return self.get(request, *args, **kwargs)
