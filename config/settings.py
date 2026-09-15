import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    value = os.environ.get(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


DEBUG = env_bool("DEBUG", True)
SECRET_KEY = os.environ.get("SECRET_KEY", "").strip()
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-local-development-only"
    else:
        raise ImproperlyConfigured(
            "The SECRET_KEY environment variable is required when DEBUG=False."
        )

ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1" if DEBUG else "",
)

CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", DEBUG)
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:3000,http://127.0.0.1:3000"
        if DEBUG
        else ""
    ),
)
CORS_ALLOW_CREDENTIALS = env_bool("CORS_ALLOW_CREDENTIALS", True)
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = os.environ.get("CSRF_COOKIE_SAMESITE", "Lax")

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-language",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

AUTH_USER_MODEL = "accounts.User"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third Party Apps
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "django_filters",
    # Local Apps
    "apps.core",
    "apps.accounts",
    "apps.services",
    "apps.projects",
    "apps.tickets",
    "apps.blog",
    "apps.billing",
      "apps.portfolio",
      "apps.reviews",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "config.middleware.AdminLanguageMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.environ.get(
            "DB_NAME",
            os.environ.get("POSTGRES_DB", "agency_db"),
        ),
        "USER": os.environ.get(
            "DB_USER",
            os.environ.get("POSTGRES_USER", "agency_user"),
        ),
        "PASSWORD": os.environ.get(
            "DB_PASSWORD",
            os.environ.get("POSTGRES_PASSWORD", "agency_secure_password"),
        ),
        "HOST": os.environ.get("DB_HOST", "db"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", "English"),
    ("fa", "فارسی"),
]
LOCALE_PATHS = [
    BASE_DIR / "locale",
]
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

PRIVATE_MEDIA_URL = "/api/v1/billing/private-files/"
PRIVATE_MEDIA_ROOT = BASE_DIR / "private_media"
PRIVATE_UPLOAD_URL = "/api/v1/core/private-files/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https")
    if env_bool("TRUST_PROXY_HEADERS", False)
    else None
)
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", not DEBUG)
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    False,
)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)
SECURE_CONTENT_TYPE_NOSNIFF = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.accounts.authentication.CookieJWTAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Default pagination and throttling settings.
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_THROTTLE_RATES": {
        "register": "5/hour",
        "email_verification": "20/hour",
        "verification_resend": "3/hour",
        "password_reset": "5/hour",
        "contact": "5/hour",
    },
}

ACCESS_TOKEN_COOKIE_NAME = os.environ.get("ACCESS_TOKEN_COOKIE_NAME", "ctrlops_access")
REFRESH_TOKEN_COOKIE_NAME = os.environ.get(
    "REFRESH_TOKEN_COOKIE_NAME", "ctrlops_refresh"
)
AUTH_COOKIE_SECURE = env_bool("AUTH_COOKIE_SECURE", not DEBUG)
AUTH_COOKIE_HTTPONLY = True
AUTH_COOKIE_SAMESITE = os.environ.get("AUTH_COOKIE_SAMESITE", "Lax")
AUTH_COOKIE_PATH = "/"
REFRESH_COOKIE_PATH = "/api/v1/accounts/"

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "CtrlOps API",
    "DESCRIPTION": "API documentation for CtrlOps web development, SEO, support, and automation services.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "config.schema.add_accept_language_header",
    ],
    "ENUM_NAME_OVERRIDES": {
        "TicketStatusEnum": "apps.tickets.models.TicketStatus",
        "TransactionStatusEnum": "apps.billing.models.TransactionStatusChoices",
    },
}

API_DOCS_ENABLED = env_bool("API_DOCS_ENABLED", DEBUG)

API_SERVER_URL = os.environ.get("API_SERVER_URL", "").strip()
if API_SERVER_URL:
    SPECTACULAR_SETTINGS["SERVERS"] = [
        {"url": API_SERVER_URL, "description": "Configured API server"},
    ]

FRONTEND_URL = os.environ.get(
    "FRONTEND_URL",
    "http://localhost:5173",
).rstrip("/")

EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_TIMEOUT = int(os.environ.get("EMAIL_TIMEOUT", "10"))
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    "CtrlOps <no-reply@ctrlops.local>",
)
EMAIL_VERIFICATION_TIMEOUT = int(os.environ.get("EMAIL_VERIFICATION_TIMEOUT", "86400"))
# Email verification tokens use Django's hardened password-reset token
# implementation and therefore share its timeout setting.
PASSWORD_RESET_TIMEOUT = EMAIL_VERIFICATION_TIMEOUT

DJANGO_LOG_LEVEL = os.environ.get("DJANGO_LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": (
                "{asctime} {levelname} {name} "
                "pid={process:d} thread={thread:d} {message}"
            ),
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": DJANGO_LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": DJANGO_LOG_LEVEL,
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
