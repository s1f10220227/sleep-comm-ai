from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Djangoのデフォルトのユーザーモデル(AbstractUser)を拡張する形で、CustomUserモデルを定義
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

    gender = models.CharField(
        max_length=12,
        choices=[('male', '男性'), ('female', '女性'), ('unspecified', '未回答')],
        default='unspecified'
    )
    age = models.IntegerField(null=True, blank=True)
