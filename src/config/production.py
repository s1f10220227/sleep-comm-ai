import os
import dj_database_url
from .settings import *

ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])

MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

DATABASES = {
    'default': dj_database_url.config()
}

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'