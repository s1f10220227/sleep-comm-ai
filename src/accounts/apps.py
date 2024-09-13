from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

# アプリケーションの設定を定義するクラスです。Djangoがこのアプリケーションを
# 認識し、適切に設定を行うために使用されます。`default_auto_field`は、
# 自動的に追加される主キーのフィールドタイプを指定します。