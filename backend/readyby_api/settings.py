"""Django settings for the ReadyBy pilot API.

Configuration is environment driven. Local development falls back to SQLite so
the pilot can be run without infrastructure; any deployment that sets
``DATABASE_URL`` uses PostgreSQL.
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import unquote, urlparse

from corsheaders.defaults import default_headers
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env(name: str, default: str = "") -> str:
    """Read an environment variable, preferring the ``DJANGO_``-prefixed form.

    ``DJANGO_DEBUG`` avoids clashing with the many unrelated ``DEBUG`` variables
    a host may already export; the bare name is still accepted.
    """
    return os.environ.get(f"DJANGO_{name}", os.environ.get(name, default))


def env_bool(name: str, default: bool = False) -> bool:
    raw = env(name)
    if not raw:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    raw = env(name)
    if not raw.strip():
        return default
    try:
        return int(raw.strip())
    except ValueError:
        raise ValueError(f"{name} must be a whole number, got {raw!r}")


def env_list(name: str, default: str = "") -> list[str]:
    raw = env(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def env_flag(name: str, default: bool = False) -> bool:
    """Read a yes/no switch from the environment."""
    raw = env(name, "").strip().lower()
    if not raw:
        return default
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a yes/no value, got {raw!r}")


def database_from_url(url: str) -> dict:
    """Translate a ``DATABASE_URL`` into Django's DATABASES shape."""
    parsed = urlparse(url)
    if parsed.scheme not in {"postgres", "postgresql", "psql"}:
        raise ValueError(f"Unsupported DATABASE_URL scheme: {parsed.scheme!r}")

    name = unquote(parsed.path.lstrip("/"))
    if not name:
        raise ValueError("DATABASE_URL is missing the database name")

    options: dict[str, object] = {}
    if parsed.port:
        options["port"] = parsed.port

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": name,
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": unquote(parsed.hostname or ""),
        "CONN_MAX_AGE": int(env("DATABASE_CONN_MAX_AGE", "60")),
        "OPTIONS": options,
    }


# --------------------------------------------------------------------------- #
#  Core
# --------------------------------------------------------------------------- #

SECRET_KEY = env("SECRET_KEY")
DEBUG = env_bool("DEBUG", False)

if not SECRET_KEY:
    if DEBUG:
        # Development convenience only. Never valid in production.
        SECRET_KEY = "django-insecure-readyby-local-development-key"
    else:
        raise RuntimeError(
            "SECRET_KEY must be set in the environment when DEBUG is False."
        )

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1" if DEBUG else "")

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "drf_spectacular",
    "accounts",
    "cafes",
    "orders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "readyby_api.urls"

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

WSGI_APPLICATION = "readyby_api.wsgi.application"
ASGI_APPLICATION = "readyby_api.asgi.application"

# --------------------------------------------------------------------------- #
#  Database
# --------------------------------------------------------------------------- #

_database_url = env("DATABASE_URL").strip()

if _database_url:
    DATABASES = {"default": database_from_url(_database_url)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------- #
#  Auth
# --------------------------------------------------------------------------- #

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Pilot: plaintext sessions are never persisted to a database and are only
# useful for the Django admin / browsable API.
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

LOGIN_URL = "/admin/login/"

# --------------------------------------------------------------------------- #
#  DRF
# --------------------------------------------------------------------------- #

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # Both schemes are accepted so an existing signed-in browser keeps
        # working while JWT becomes the default for new clients.
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("THROTTLE_ANON_PER_MIN", "120/min"),
        "user": env("THROTTLE_USER_PER_MIN", "300/min"),
        "login": env("THROTTLE_LOGIN_PER_MIN", "10/min"),
        "order_create": env("THROTTLE_ORDER_CREATE_PER_MIN", "20/min"),
        "order_status": env("THROTTLE_ORDER_STATUS_PER_MIN", "120/min"),
    },
    "EXCEPTION_HANDLER": "readyby_api.exceptions.api_exception_handler",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

# --------------------------------------------------------------------------- #
#  JWT
# --------------------------------------------------------------------------- #

# The signing key reuses SECRET_KEY, so there is no second secret to leak or
# rotate. An unset key would silently fall back to Django's own SECRET_KEY.
SIMPLE_JWT = {
    "SIGNING_KEY": SECRET_KEY,
    "ALGORITHM": "HS256",
    # A café session has to survive a whole shift behind the bar.
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(env("JWT_ACCESS_MINUTES", str(12 * 60)))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(env("JWT_REFRESH_DAYS", "7"))
    ),
    "ROTATE_REFRESH_TOKENS": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ReadyBy Pilot API",
    "DESCRIPTION": (
        "Order-ahead pickup API for the ReadyBy pilot. Customers choose a "
        "destination and an arrival time, order from a participating cafe, and "
        "collect the order at the counter. Payment is taken at pickup."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# --------------------------------------------------------------------------- #
#  CORS
# --------------------------------------------------------------------------- #

# The origins to trust when CORS is not wide open. Keep this in step with
# CORS_ALLOWED_ORIGINS in backend/.env for anything other than local dev.
LOCAL_FRONTEND_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.1.177:3000",
)

# Every spelling of this machine is a *different* browser origin: localhost,
# 127.0.0.1, the WiFi address (192.168.x.x) and the WSL adapter address are all
# distinct to the browser, and Next.js happily serves on every one of them. An
# allowlist has to be updated for each, and a missing entry is invisible: Django
# answers 200, the browser throws the response away, and the page reports that
# the server "isn't answering" - the same symptom as a dead process.
#
# So local development accepts any origin. Production (DEBUG=False) never does:
# it requires an explicit allowlist, because there the origin is fixed and known.
CORS_ALLOW_ALL_ORIGINS = DEBUG and not env_flag("DJANGO_CORS_STRICT", False)

CORS_ALLOWED_ORIGINS = (
    []
    if CORS_ALLOW_ALL_ORIGINS
    else env_list("CORS_ALLOWED_ORIGINS", ",".join(LOCAL_FRONTEND_ORIGINS))
)
CORS_ALLOW_CREDENTIALS = False
CORS_URLS_REGEX = r"^/api/.*$"

# Any request carrying a non-safelisted header has to pass a CORS preflight
# first, and the preflight only succeeds if the server echoes that header back
# in Access-Control-Allow-Headers. Django's default list covers the auth and
# content-type headers the rest of the app sends, but not Idempotency-Key, which
# createOrder() attaches to POST /api/orders/new/. So the place-order preflight
# failed, the browser discarded the response and fetch() rejected with a
# TypeError - indistinguishable, to the frontend, from the API being down.
# Widening CORS_ALLOW_ALL_ORIGINS does not help: that governs origins only.
CORS_ALLOW_HEADERS = list(default_headers) + ["idempotency-key"]

# --------------------------------------------------------------------------- #
#  Internationalisation
# --------------------------------------------------------------------------- #

LANGUAGE_CODE = "en-gb"
TIME_ZONE = env("TIME_ZONE", "Europe/London")
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------- #
#  Static files
# --------------------------------------------------------------------------- #

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
WHITENOISE_AUTOREFRESH = DEBUG

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# --------------------------------------------------------------------------- #
#  Security (applies whenever DEBUG is False)
# --------------------------------------------------------------------------- #

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", not DEBUG)
SECURE_HSTS_SECONDS = int(env("SECURE_HSTS_SECONDS", "0" if DEBUG else "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = False
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True

DATA_UPLOAD_MAX_MEMORY_SIZE = int(env("DATA_UPLOAD_MAX_MEMORY_SIZE", str(2_621_440)))
DATA_UPLOAD_MAX_NUMBER_FIELDS = 100

# --------------------------------------------------------------------------- #
#  Booking rules
# --------------------------------------------------------------------------- #

# How strict the arrival-time window is. A café with a slower kitchen raises
# MINIMUM_LEAD_MINUTES rather than editing code. See readyby/ready_by.py.
READYBY_RULES = {
    "PREPARATION_BUFFER_MINUTES": env_int("PREPARATION_BUFFER_MINUTES", 2),
    "MINIMUM_LEAD_MINUTES": env_int("MINIMUM_LEAD_MINUTES", 5),
    "MAX_BOOKING_HORIZON_HOURS": env_int("MAX_BOOKING_HORIZON_HOURS", 24),
    "COLLECTION_GRACE_MINUTES": env_int("COLLECTION_GRACE_MINUTES", 30),
}

# --------------------------------------------------------------------------- #
#  Pilot data
# --------------------------------------------------------------------------- #

# Demo cafes are fictional. They are only exposed when explicitly enabled so a
# real pilot customer can never be shown a made-up cafe.
SHOW_DEMO_CAFES = env_bool("SHOW_DEMO_CAFES", False)

# --------------------------------------------------------------------------- #
#  Logging
# --------------------------------------------------------------------------- #

LOG_LEVEL = env("LOG_LEVEL", "DEBUG" if DEBUG else "INFO").upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING" if not DEBUG else "INFO",
            "propagate": False,
        },
        "accounts": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "cafes": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "orders": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
    },
}