from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from .models import User


class CookieTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Return a useful, machine-readable error for unverified accounts."""

    default_error_messages = {
        **TokenObtainPairSerializer.default_error_messages,
        "email_not_verified": _("Email address has not been verified."),
    }

    def validate(self, attrs):
        email = attrs.get(self.username_field, "").strip().lower()
        user = User.objects.filter(email__iexact=email).only(
            "is_email_verified"
        ).first()
        if user is not None and not user.is_email_verified:
            raise AuthenticationFailed(
                self.error_messages["email_not_verified"],
                code="email_not_verified",
            )
        return super().validate(attrs)


class CookieTokenRefreshSerializer(TokenRefreshSerializer):
    pass
