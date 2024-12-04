import os
import dj_database_url
from .settings import *

# ALLOWED_HOSTS に Render ドメインを追加
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# WhiteNoise ミドルウェア
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# データベース設定 (DATABASE_URL を利用)
DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
}

# 静的ファイルの設定
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
