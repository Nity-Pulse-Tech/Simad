from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from simad.core.models import SIMADBASEMODEL
from simad.global_data.enum import GenderChoices
from simad.global_data.enum import UserTypeChoices
from simad.users.managers import UserManager


class User(AbstractUser, SIMADBASEMODEL):
    """
    Default custom user model for SIMAD.

    Authentication supports both email and phone number.
    New users are inactive (is_active=False) until they verify
    via email or phone OTP.
    """

    username = None  # type: ignore[assignment]

    first_name = models.CharField(_("First Name"), max_length=100, blank=True, default="")
    last_name = models.CharField(_("Last Name"), max_length=100, blank=True, default="")
    email = models.EmailField(_("Email Address"), unique=True, blank=True, null=True)
    phone_number = models.CharField(
        _("Phone Number"),
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text=_("Used as an alternative login identifier and for OTP verification."),
    )
    user_type = models.CharField(
        _("User Type"),
        max_length=50,
        choices=UserTypeChoices.choices,
        default=UserTypeChoices.CUSTOMER,
    )
    is_active = models.BooleanField(
        _("Active"),
        default=False,
        help_text=_(
            "Designates whether this user account should be considered active. "
            "Users must verify their email or phone number before being activated."
        ),
    )
    is_email_verified = models.BooleanField(_("Email Verified"), default=False)
    is_phone_verified = models.BooleanField(_("Phone Verified"), default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone_number"]

    objects = UserManager()

    class Meta(AbstractUser.Meta):
        swappable = "AUTH_USER_MODEL"
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return self.email or self.phone_number or str(self.id)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class UserProfile(SIMADBASEMODEL):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    bio = models.TextField(_("Bio"), blank=True)
    birth_date = models.DateField(_("Birth Date"), null=True, blank=True)
    gender = models.CharField(
        _("Gender"),
        max_length=20,
        choices=GenderChoices.choices,
        default=GenderChoices.OTHER,
    )
    avatar = models.ImageField(
        _("Avatar"), upload_to="avatars/", null=True, blank=True
    )

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        return f"Profile of {self.user}"


class Address(SIMADBASEMODEL):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="addresses"
    )
    address_line1 = models.CharField(_("Address Line 1"), max_length=255, default="")
    address_line2 = models.CharField(_("Address Line 2"), max_length=255, blank=True, default="")
    city = models.CharField(_("City"), max_length=100, default="")
    state_province = models.CharField(_("State / Province"), max_length=100, default="")
    postal_code = models.CharField(_("Postal Code"), max_length=20, default="")
    country = models.CharField(_("Country"), max_length=100, default="")
    is_default = models.BooleanField(_("Default Address"), default=False)

    class Meta:
        verbose_name = _("Address")
        verbose_name_plural = _("Addresses")

    def __str__(self):
        return f"{self.address_line1}, {self.city}"
