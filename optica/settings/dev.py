from .base import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# En dev no necesitamos el manifest de collectstatic
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
