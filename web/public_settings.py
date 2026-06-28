from .settings import *


DEBUG = False
PUBLIC_SITE_ONLY = True

STATIC_URL = '/static/'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
SITE_ID = 1
