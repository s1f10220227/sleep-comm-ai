from django.contrib import admin
from .models import CustomUser

# 管理画面でCustomUserモデルを登録することで、Djangoの管理画面から
# このモデルのデータを操作できるようにします。
admin.site.register(CustomUser)
