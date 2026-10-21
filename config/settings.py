"""Django settings for the clinic management system."""
import os
from pathlib import Path
import dj_database_url


from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
)
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "core",
    "accounts",
    "patients",
    "appointments",
    "encounters",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "accounts.middleware.ForcePasswordChangeMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.clinic",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# DJANGO_DB_PATH lets a container keep SQLite on a mounted volume (e.g. /app/data).
# The timeout reduces "database is locked" errors with multiple Gunicorn workers.
# DB_PATH = os.getenv("DJANGO_DB_PATH")
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": Path(DB_PATH) if DB_PATH else BASE_DIR / "db.sqlite3",
#         "OPTIONS": {"timeout": 20},
#     }
# }




DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
        )
    }
else:
    DB_PATH = os.environ.get("DJANGO_DB_PATH")

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": Path(DB_PATH) if DB_PATH else BASE_DIR / "db.sqlite3",
            "OPTIONS": {"timeout": 20},
        }
    }

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("TIME_ZONE", "Africa/Lagos")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise serves compressed static files from STATIC_ROOT in production,
# so Gunicorn can serve the whole app without a separate web server.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

SESSION_COOKIE_AGE = 60 * 60 * 12  # A clinical shift.
SESSION_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True

# Clinic identity, used throughout the interface and on printed documents.
CLINIC_NAME = os.getenv("CLINIC_NAME", "Specialist Eye Care Centre")
CLINIC_TAGLINE = os.getenv("CLINIC_TAGLINE", "Comprehensive eye care")
CLINIC_ADDRESS = os.getenv("CLINIC_ADDRESS", "12 Vision Way, Lagos")
CLINIC_PHONE = os.getenv("CLINIC_PHONE", "+234 800 000 0000")
CLINIC_EMAIL = os.getenv("CLINIC_EMAIL", "hello@suavedef.example")

# Set DJANGO_BEHIND_PROXY=True when TLS terminates at a reverse proxy in front
# of Gunicorn (the proxy must send X-Forwarded-Proto).
if env_bool("DJANGO_BEHIND_PROXY", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# The container healthcheck is a plain-HTTP request and must not be redirected.
SECURE_REDIRECT_EXEMPT = [r"^healthz/?$"]

if not DEBUG:
    # Defaults are secure; a plain-HTTP trial deployment must opt out explicitly.
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
    SECURE_COOKIES = env_bool("DJANGO_SECURE_COOKIES", SECURE_SSL_REDIRECT)
    SESSION_COOKIE_SECURE = SECURE_COOKIES
    CSRF_COOKIE_SECURE = SECURE_COOKIES
    SECURE_HSTS_SECONDS = 31536000 if SECURE_SSL_REDIRECT else 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = bool(SECURE_HSTS_SECONDS)
    SECURE_HSTS_PRELOAD = bool(SECURE_HSTS_SECONDS)
