"""
Django settings for fcms_project.
Phase 1: auth + roles + clubs working; other apps registered as shells.
"""

from pathlib import Path
import os

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# --- SECURITY ---
# Locally, falls back to the insecure dev key below. On Render, set SECRET_KEY
# as an environment variable (the render.yaml blueprint generates one for you).
# IMPORTANT: if SECRET_KEY isn't pinned as a persistent env var on Render,
# every restart/redeploy invalidates all existing sessions and CSRF cookies —
# double check this is set under your Render service's Environment tab.
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-CHANGE-ME-before-deployment")

DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = ["fcms-0q0x.onrender.com" ,"localhost", "127.0.0.1"]

# Render sets this automatically for every web service — no manual config needed.
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Single source of truth for CSRF_TRUSTED_ORIGINS — previously this was set
# twice in this file (once here, once again hardcoded near the bottom), with
# the second definition silently overwriting the first. Only one definition
# now, always including both the known production domain and whatever
# RENDER_EXTERNAL_HOSTNAME resolves to for this deploy.
CSRF_TRUSTED_ORIGINS = ["https://fcms-0q0x.onrender.com"]
if RENDER_EXTERNAL_HOSTNAME:
    render_origin = f"https://{RENDER_EXTERNAL_HOSTNAME}"
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)

# Render terminates TLS at its proxy and forwards to the app over plain HTTP
# internally. Without this, Django can't tell the original request was HTTPS,
# which affects request.is_secure() and, in turn, secure-cookie and CSRF
# behavior.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --- APPLICATIONS ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "crispy_forms",
    "crispy_bootstrap5",
    # FCMS apps — one per module, matching the MVP doc
    "accounts",
    "clubs",
    "players",
    "coaches",
    "referees",
    "seasons",
    "competitions",
    "fixtures",
    "results.apps.ResultsConfig",  # custom app config to register signals
    "standings",
    "reports",
    "dashboard",
    "transfers",
    "lineups",
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
]

ROOT_URLCONF = "foot.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "foot.wsgi.application"

# --- DATABASE ---
# Locally (no DATABASE_URL set): same SQLite file as before.
# On Render: DATABASE_URL is provided automatically and Postgres is used instead.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=not DEBUG,
    )
}

# --- CUSTOM USER MODEL ---
AUTH_USER_MODEL = "accounts.CustomUser"

# --- PASSWORD VALIDATION ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- LOGIN / LOGOUT REDIRECTS ---
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "accounts:login"

# --- INTERNATIONALIZATION ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True

# --- STATIC & MEDIA FILES ---
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- CRISPY FORMS ---
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"