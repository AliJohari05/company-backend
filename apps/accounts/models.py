from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Email address is required."))
        email = self.normalize_email(email).strip().lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_email_verified", True)
        extra_fields.setdefault("role", UserRole.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


class UserRole(models.TextChoices):
    ADMIN = "ADMIN", _("Administrator")
    STAFF = "STAFF", _("Staff")
    CLIENT = "CLIENT", _("Client")


class User(AbstractUser, TimeStampedModel):
    username = None

    email = models.EmailField(_("Email Address"), unique=True)

    is_email_verified = models.BooleanField(
        _("Email Verified"),
        default=False,
    )

    email_verified_at = models.DateTimeField(
        _("Email Verified At"),
        null=True,
        blank=True,
    )

    phone_number = models.CharField(
        _("Phone Number"), max_length=15, blank=True, null=True
    )
    company_name = models.CharField(
        _("Company Name"), max_length=100, blank=True, null=True
    )
    role = models.CharField(
        _("User Role"), max_length=10, choices=UserRole.choices, default=UserRole.CLIENT
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
