from .settings import *


SECRET_KEY = os.environ.get("SECRET_KEY", "local-development-only")
DEBUG = True

STATIC_URL = "/static/"
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
SITE_ID = 1
