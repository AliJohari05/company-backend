from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication


class CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        return reason


def enforce_csrf(request):
    csrf_check = CSRFCheck(lambda _request: None)
    csrf_check.process_request(request)
    header_key = "HTTP_X_CSRFTOKEN"
    original_header = request.META.get(header_key)
    candidates = (
        [value.strip() for value in original_header.split(",")]
        if original_header and "," in original_header
        else [original_header]
    )
    reason = None
    for candidate in candidates:
        if not candidate:
            continue
        request.META[header_key] = candidate
        reason = csrf_check.process_view(request, None, (), {})
        if reason is None:
            break
    else:
        request.META[header_key] = original_header or ""
        reason = csrf_check.process_view(request, None, (), {})

    if original_header is not None:
        request.META[header_key] = original_header
    else:
        request.META.pop(header_key, None)
    if reason:
        raise exceptions.PermissionDenied(f"CSRF validation failed: {reason}")


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticate browser requests with an access-token cookie."""

    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE_NAME)
        if raw_token:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            enforce_csrf(request)
            return user, validated_token

        return super().authenticate(request)
