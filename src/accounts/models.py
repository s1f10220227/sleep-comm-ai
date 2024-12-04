from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # 他のフィールドの定義
    # Djangoのデフォルトのユーザーモデル(AbstractUser)を拡張する形で、
    # CustomUserモデルを定義します。
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    gender = models.CharField(max_length=12, choices=[('male', '男性'), ('female', '女性'), ('unspecified', '未回答')], default='unspecified')
    age = models.IntegerField(null=True, blank=True)

# `groups`と`user_permissions`は、ユーザーが所属するグループや
    # 特定の権限を設定するためのフィールドです。DjangoのデフォルトのUserモデルの
    # 関連を保持しつつ、関連名をカスタムします。
