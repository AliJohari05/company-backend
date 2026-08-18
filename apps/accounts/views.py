from functools import partial

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .emails import send_verification_email
from .serializers import (
    ChangePasswordSerializer,
    DetailResponseSerializer,
    LogoutSerializer,
    RegisterSerializer,
    RegisterResponseSerializer,
    ResendVerificationSerializer,
    UserProfileSerializer,
    VerifyEmailSerializer,
)
from .tokens import email_verification_token

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'register'

    @extend_schema(
        responses={201: RegisterResponseSerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = serializer.save()
            transaction.on_commit(
                partial(send_verification_email, user),
                robust=True,
            )

        return Response(
            {
                'detail': _(
                    'Registration successful. Please verify your email address.'
                ),
                'email': user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = VerifyEmailSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'email_verification'

    @extend_schema(
        request=VerifyEmailSerializer,
        responses={
            200: DetailResponseSerializer,
            400: DetailResponseSerializer,
        },
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user_id = force_str(
                urlsafe_base64_decode(serializer.validated_data['uid'])
            )
        except (TypeError, ValueError, OverflowError):
            return self._invalid_token_response()

        with transaction.atomic():
            try:
                user = User.objects.select_for_update().get(pk=user_id)
            except (User.DoesNotExist, ValueError, TypeError, OverflowError):
                return self._invalid_token_response()

            if not email_verification_token.check_token(
                user,
                serializer.validated_data['token'],
            ):
                return self._invalid_token_response()

            if user.is_email_verified:
                return Response(
                    {'detail': _('Email address is already verified.')},
                    status=status.HTTP_200_OK,
                )

            user.is_email_verified = True
            user.is_active = True
            user.email_verified_at = timezone.now()
            user.save(
                update_fields=(
                    'is_email_verified',
                    'is_active',
                    'email_verified_at',
                    'updated_at',
                )
            )

        return Response(
            {'detail': _('Email address verified successfully.')},
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _invalid_token_response():
        return Response(
            {'detail': _('The verification link is invalid or has expired.')},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ResendVerificationEmailView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = ResendVerificationSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'verification_resend'

    @extend_schema(
        request=ResendVerificationSerializer,
        responses={200: DetailResponseSerializer},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        user = User.objects.filter(
            email__iexact=email,
            is_email_verified=False,
        ).first()
        if user is not None:
            transaction.on_commit(
                partial(send_verification_email, user),
                robust=True,
            )

        return Response(
            {
                'detail': _(
                    'If an eligible account exists, a verification email '
                    'has been sent.'
                )
            },
            status=status.HTTP_200_OK,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class LogoutView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = LogoutSerializer

    @extend_schema(
        request=LogoutSerializer,
        responses={
            205: DetailResponseSerializer,
            400: DetailResponseSerializer,
        },
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh_token = serializer.validated_data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": _("Successfully logged out.")}, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            return Response({"detail": _("Invalid token.")}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": [_("Wrong password.")]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"detail": _("Password updated successfully.")}, status=status.HTTP_200_OK)
