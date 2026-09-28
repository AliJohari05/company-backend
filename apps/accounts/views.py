from functools import partial

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .auth_serializers import (
    CookieTokenObtainPairSerializer,
    CookieTokenRefreshSerializer,
)
from .authentication import enforce_csrf
from .serializers import (
    ChangePasswordSerializer,
    CSRFTokenResponseSerializer,
    DetailResponseSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterResponseSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    UserProfileSerializer,
    VerifyEmailSerializer,
)
from .tasks import send_password_reset_email_task, send_verification_email_task
from .tokens import email_verification_token, password_reset_token

User = get_user_model()


def _set_auth_cookies(response, token_data):
    response.set_cookie(
        settings.ACCESS_TOKEN_COOKIE_NAME,
        token_data["access"],
        max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        httponly=settings.AUTH_COOKIE_HTTPONLY,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path=settings.AUTH_COOKIE_PATH,
    )
    response.set_cookie(
        settings.REFRESH_TOKEN_COOKIE_NAME,
        token_data.get("refresh", ""),
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        httponly=settings.AUTH_COOKIE_HTTPONLY,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path=settings.REFRESH_COOKIE_PATH,
    )
    return response


class CookieTokenObtainPairView(TokenObtainPairView):
    serializer_class = CookieTokenObtainPairSerializer

    @extend_schema(
        responses={200: OpenApiResponse(description="Authentication cookies set.")},
    )
    def post(self, request, *args, **kwargs):
        enforce_csrf(request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = Response(
            {"detail": _("Login successful.")},
            status=status.HTTP_200_OK,
        )
        return _set_auth_cookies(response, serializer.validated_data)


class CookieTokenRefreshView(TokenRefreshView):
    serializer_class = CookieTokenRefreshSerializer

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Authentication cookies refreshed.")
        },
    )
    def post(self, request, *args, **kwargs):
        enforce_csrf(request)
        refresh = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)
        if not refresh:
            return Response(
                {"detail": _("Refresh token cookie is missing.")},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        serializer = self.get_serializer(data={"refresh": refresh})
        serializer.is_valid(raise_exception=True)
        response = Response(
            {"detail": _("Token refreshed successfully.")},
            status=status.HTTP_200_OK,
        )
        return _set_auth_cookies(response, serializer.validated_data)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CSRFTokenView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        responses={200: CSRFTokenResponseSerializer},
    )
    def get(self, request):
        return Response(
            {
                "detail": _("CSRF cookie set."),
                "csrf_token": get_token(request),
            }
        )


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    @extend_schema(
        responses={201: RegisterResponseSerializer},
    )
    def create(self, request, *args, **kwargs):
        enforce_csrf(request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = serializer.save()
            transaction.on_commit(
                partial(send_verification_email_task.delay, user.pk),
                robust=True,
            )

        return Response(
            {
                "detail": _(
                    "Registration successful. Please verify your email address."
                ),
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = VerifyEmailSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "email_verification"

    @extend_schema(
        request=VerifyEmailSerializer,
        responses={
            200: DetailResponseSerializer,
            400: DetailResponseSerializer,
        },
    )
    def post(self, request):
        enforce_csrf(request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user_id = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
        except (TypeError, ValueError, OverflowError):
            return self._invalid_token_response()

        with transaction.atomic():
            try:
                user = User.objects.select_for_update().get(pk=user_id)
            except (User.DoesNotExist, ValueError, TypeError, OverflowError):
                return self._invalid_token_response()

            if not email_verification_token.check_token(
                user,
                serializer.validated_data["token"],
            ):
                return self._invalid_token_response()

            if user.is_email_verified:
                return Response(
                    {"detail": _("Email address is already verified.")},
                    status=status.HTTP_200_OK,
                )

            user.is_email_verified = True
            user.is_active = True
            user.email_verified_at = timezone.now()
            user.save(
                update_fields=(
                    "is_email_verified",
                    "is_active",
                    "email_verified_at",
                    "updated_at",
                )
            )

        return Response(
            {"detail": _("Email address verified successfully.")},
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _invalid_token_response():
        return Response(
            {"detail": _("The verification link is invalid or has expired.")},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ResendVerificationEmailView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = ResendVerificationSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "verification_resend"

    @extend_schema(
        request=ResendVerificationSerializer,
        responses={200: DetailResponseSerializer},
    )
    def post(self, request):
        enforce_csrf(request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(
            email__iexact=email,
            is_email_verified=False,
        ).first()
        if user is not None:
            transaction.on_commit(
                partial(send_verification_email_task.delay, user.pk),
                robust=True,
            )

        return Response(
            {
                "detail": _(
                    "If an eligible account exists, a verification email "
                    "has been sent."
                )
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = PasswordResetRequestSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request):
        enforce_csrf(request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(
            email__iexact=serializer.validated_data["email"],
            is_active=True,
            is_email_verified=True,
        ).first()
        if user is not None:
            transaction.on_commit(
                partial(send_password_reset_email_task.delay, user.pk),
                robust=True,
            )
        return Response(
            {"detail": _("If an eligible account exists, a reset email has been sent.")}
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        enforce_csrf(request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user_id = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, TypeError, ValueError, OverflowError):
            return self._invalid_token_response()

        if not password_reset_token.check_token(user, serializer.validated_data["token"]):
            return self._invalid_token_response()

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=("password", "updated_at"))
        return Response({"detail": _("Password reset successfully.")})

    @staticmethod
    def _invalid_token_response():
        return Response(
            {"detail": _("The password reset link is invalid or has expired.")},
            status=status.HTTP_400_BAD_REQUEST,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class LogoutView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = DetailResponseSerializer

    @extend_schema(
        responses={
            205: DetailResponseSerializer,
            400: DetailResponseSerializer,
        },
    )
    def post(self, request):
        enforce_csrf(request)

        try:
            refresh_token = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)
            if not refresh_token:
                raise TokenError("Refresh token cookie is missing.")
            token = RefreshToken(refresh_token)
            token.blacklist()
            response = Response(
                {"detail": _("Successfully logged out.")},
                status=status.HTTP_205_RESET_CONTENT,
            )
            response.delete_cookie(
                settings.ACCESS_TOKEN_COOKIE_NAME,
                path=settings.AUTH_COOKIE_PATH,
            )
            response.delete_cookie(
                settings.REFRESH_TOKEN_COOKIE_NAME,
                path=settings.REFRESH_COOKIE_PATH,
            )
            return response
        except TokenError:
            return Response(
                {"detail": _("Invalid token.")}, status=status.HTTP_400_BAD_REQUEST
            )


class ChangePasswordView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"old_password": [_("Wrong password.")]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response(
            {"detail": _("Password updated successfully.")}, status=status.HTTP_200_OK
        )
