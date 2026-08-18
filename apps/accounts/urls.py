from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    ChangePasswordView,
    LogoutView,
    RegisterView,
    ResendVerificationEmailView,
    UserProfileView,
    VerifyEmailView,
)

urlpatterns = [
    # Auth & Tokens
    path('register/', RegisterView.as_view(), name='auth_register'),
    path(
        'verify-email/',
        VerifyEmailView.as_view(),
        name='verify_email',
    ),
    path(
        'resend-verification/',
        ResendVerificationEmailView.as_view(),
        name='resend_verification',
    ),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    
    # Profile & Security
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
]
