from drf_spectacular.extensions import OpenApiAuthenticationExtension


class CookieJWTAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = "apps.accounts.authentication.CookieJWTAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
