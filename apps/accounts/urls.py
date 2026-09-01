from django.urls import path

from .views import (
    ChangePasswordView,
    CSRFTokenView,
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    LogoutView,
    RegisterView,
    ResendVerificationEmailView,
    UserProfileView,
    VerifyEmailView,
)

urlpatterns = [
    # Auth & Tokens
    path("register/", RegisterView.as_view(), name="auth_register"),
    path(
        "verify-email/",
        VerifyEmailView.as_view(),
        name="verify_email",
    ),
    path(
        "resend-verification/",
        ResendVerificationEmailView.as_view(),
        name="resend_verification",
    ),
    path("csrf/", CSRFTokenView.as_view(), name="csrf_token"),
    path("login/", CookieTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="auth_logout"),
    # Profile & Security
    path("profile/", UserProfileView.as_view(), name="user_profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
]
