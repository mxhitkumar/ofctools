from .base import *
import os
import sys
import ast
import pytz
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv('.env')

DEBUG = True

ALLOWED_HOSTS = ["*"]

# PostgreSQL local development database

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Static & Media
STATIC_URL = "/static/"
MEDIA_URL = "/media/"

STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_ROOT = BASE_DIR / "media"

# Email backend (console)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# CORS (optional)
CORS_ALLOW_ALL_ORIGINS = True
