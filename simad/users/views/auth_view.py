import uuid
import random
import logging
import time
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.shortcuts import redirect, render
from django.views.generic import TemplateView, View
from django.urls import reverse_lazy, reverse
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.db import transaction
from ..models import User
from ..utils import send_whatsapp_verification_link

logger = logging.getLogger(__name__)

class LoginView(TemplateView):
    template_name = "pages/auth/login.html"

    def post(self, request, *args, **kwargs):
        login_id = request.POST.get('login')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember-me') == 'on'

        if not login_id or not password:
            messages.error(request, "Please enter both login identifier and password.")
            return self.get(request, *args, **kwargs)

        from django.contrib.auth import authenticate, login
        user = authenticate(request, username=login_id, password=password)

        if user:
            if not user.is_active:
                messages.error(request, "Your account is not active. Please verify your email or phone number.")
                request.session['verification_email'] = user.email
                if user.is_phone_verified: # Simple logic to guess method
                     request.session['verification_method'] = 'whatsapp'
                     return redirect('users:whatsapp-sent')
                else:
                     request.session['verification_method'] = 'email'
                     return redirect('users:verify-code')

            login(request, user, backend='simad.users.backends.MultiMethodBackend')
            if not remember_me:
                request.session.set_expiry(0)
            
            logger.info(f"User {login_id} logged in successfully.")
            return render(request, self.template_name, {'delayed_redirect_url': reverse('core:home')})
        else:
            logger.warning(f"Failed login attempt for {login_id}.")
            messages.error(request, "Invalid login credentials.")
            return self.get(request, *args, **kwargs)

class SignupView(TemplateView):
    template_name = "pages/auth/signup.html"

    @transaction.atomic
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
        
        logger.info(f"New user created: {email}, activation method: {verification_method}")

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
            logger.info(f"Email verification sent to {email}")
        elif verification_method == 'whatsapp':
            # Generate a unique token for WhatsApp verification (since it's a link)
            token = str(uuid.uuid4())
            cache_key = f"whatsapp_activation_{token}"
            cache.set(cache_key, email, timeout=86400) # Valid for 24 hours
            
            # Construct the activation URL
            activation_url = request.build_absolute_uri(
                reverse('users:activate-account', kwargs={'token': token})
            )
            
            # Send WhatsApp via Meta Cloud API
            send_whatsapp_verification_link(user, activation_url)
            
            messages.info(request, "A verification link has been sent to your WhatsApp.")
            request.session['verification_email'] = email
            return render(request, self.template_name, {'delayed_redirect_url': reverse('users:whatsapp-sent')})
        
        # Store verification info in session
        request.session['verification_email'] = email
        request.session['verification_method'] = verification_method
        
        messages.success(request, f"Account created! A verification code has been sent to {email}.")
        return render(request, self.template_name, {'delayed_redirect_url': reverse('users:verify-code')})

class VerifyCodeView(TemplateView):
    template_name = "pages/auth/verify_code.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        email = self.request.session.get('verification_email')
        if email:
            context['resend_count'] = cache.get(f"resend_count_{email}", 0)
        return context

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
            request.session.pop('verification_email', None)
            
            logger.info(f"User {email} successfully verified via OTP.")
            messages.success(request, "Account verified successfully!")
            return render(request, self.template_name, {'delayed_redirect_url': reverse('core:home')})
        else:
            logger.warning(f"Failed verification attempt for {email}. Incorrect code: {entered_code}")
            messages.error(request, "Invalid or expired code.")
            return self.get(request, *args, **kwargs)

class WhatsAppSentView(TemplateView):
    template_name = "pages/auth/whatsapp_sent.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        email = self.request.session.get('verification_email')
        context['email'] = email
        if email:
            context['resend_count'] = cache.get(f"resend_count_{email}", 0)
        return context

class ActivateAccountView(View):
    def get(self, request, token, *args, **kwargs):
        cache_key = f"whatsapp_activation_{token}"
        email = cache.get(cache_key)
        
        if not email:
            messages.error(request, "Link is invalid or has expired.")
            return redirect('users:signup')
            
        try:
            user = User.objects.get(email=email)
            user.is_active = True
            user.is_email_verified = True # Or WhatsApp verified if we add the field
            user.save()
            
            # Log the user in
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # Cleanup
            cache.delete(cache_key)
            request.session.pop('verification_email', None)
                
            messages.success(request, "Account activated successfully! Welcome to SIMAD.")
            return redirect('core:home')
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('users:signup')

class ResendVerificationView(View):
    def post(self, request, *args, **kwargs):
        email = request.session.get('verification_email')
        if not email:
            return redirect('users:signup')
            
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return redirect('users:signup')

        # Throttling logic
        cooldown_key = f"resend_cooldown_{email}"
        count_key = f"resend_count_{email}"
        
        if cache.get(cooldown_key):
            messages.error(request, "Please wait before requesting another message.")
            return redirect(request.META.get('HTTP_REFERER', 'users:signup'))
            
        resend_count = cache.get(count_key, 0)
        
        # Determine verification method from session
        verification_method = request.session.get('verification_method', 'email')
            
        if verification_method == 'email':
            # Regenerate OTP
            otp = str(random.randint(100000, 999999))
            cache.set(f"otp_verification_{email}", otp, timeout=600)
            
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
            logger.info(f"Email verification RESENT to {email}")
            messages.success(request, f"A new code has been sent to {email}.")
        else:
            # Regenerate Token
            token = str(uuid.uuid4())
            cache.set(f"whatsapp_activation_{token}", email, timeout=86400)
            activation_url = request.build_absolute_uri(
                reverse('users:activate-account', kwargs={'token': token})
            )
            send_whatsapp_verification_link(user, activation_url)
            logger.info(f"WhatsApp verification RESENT to {user.phone_number}")
            messages.success(request, "A new link has been sent to your WhatsApp.")
            
        # Set cooldown for next resend
        cooldown_time = 60 if resend_count == 0 else 120
        cache.set(cooldown_key, True, timeout=cooldown_time)
        cache.set(count_key, resend_count + 1, timeout=3600) # Reset count after 1 hour
        
        return redirect(request.META.get('HTTP_REFERER', 'users:signup'))

class LogoutView(View):
    def post(self, request, *args, **kwargs):
        from django.contrib.auth import logout
        logout(request)
        messages.info(request, "Vous avez été déconnecté avec succès.")
        return render(request, 'pages/home/home.html', {'delayed_redirect_url': reverse('core:home')})
