from .base import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Email simulado: imprime en stdout del contenedor (no envía correos reales)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@optica-demo.local"
