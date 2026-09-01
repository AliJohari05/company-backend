from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)


class CookieTokenObtainPairSerializer(TokenObtainPairSerializer):
    pass


class CookieTokenRefreshSerializer(TokenRefreshSerializer):
    pass
