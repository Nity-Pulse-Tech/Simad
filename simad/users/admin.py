from allauth.account.decorators import secure_admin_login
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.utils.translation import gettext_lazy as _

from .forms import UserAdminChangeForm
from .forms import UserAdminCreationForm
from .models import Address
from .models import User
from .models import UserProfile

if settings.DJANGO_ADMIN_FORCE_ALLAUTH:
    # Force the `admin` sign in process to go through the `django-allauth` workflow:
    # https://docs.allauth.org/en/latest/common/admin.html#admin
    admin.autodiscover()
    admin.site.login = secure_admin_login(admin.site.login)  # type: ignore[method-assign]


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = _("Profile")


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    inlines = [UserProfileInline, AddressInline]
    
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "phone_number", "user_type")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_email_verified",
                    "is_phone_verified",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            _("Consent"),
            {"fields": ("terms_accepted", "terms_accepted_at")},
        ),
        (
            _("Important dates"),
            {"fields": ("last_login", "date_joined", "created", "modified")},
        ),
    )
    list_display = ["email", "full_name_display", "phone_number", "user_type", "is_active", "is_staff"]
    list_filter = ["user_type", "is_active", "is_staff", "is_superuser", "is_email_verified", "is_phone_verified"]
    search_fields = ["email", "first_name", "last_name", "phone_number"]
    ordering = ["-created"]
    readonly_fields = ["created", "modified", "terms_accepted_at"]
    
    @admin.display(description=_("Full Name"))
    def full_name_display(self, obj):
        return obj.full_name

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "phone_number", "password1", "password2"),
            },
        ),
    )
