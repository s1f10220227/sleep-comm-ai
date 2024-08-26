from django.db import models
import uuid
from django.contrib.postgres.fields import JSONField

# ユーザーモデル
class User(models.Model):
    # UUIDフィールドはユーザーの一意識別子
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    # メールアドレスフィールド、ユニークかつnull不可
    email = models.EmailField(unique=True, null=False)
    # パスワードフィールド、null不可
    password = models.CharField(max_length=128, null=False)
    # プロフィール情報をJSON形式で保存
    profile_info = JSONField(blank=True, null=True)
    # 初期の睡眠の質（1-10の整数値）
    sleep_quality_initial = models.IntegerField(null=True, blank=True)
    # 最終の睡眠の質（1-10の整数値）
    sleep_quality_final = models.IntegerField(null=True, blank=True)
    # アカウント作成日時、自動的に現在の日時が設定される
    created_at = models.DateTimeField(auto_now_add=True)
    # 最終更新日時、更新されるたびに現在の日時が設定される
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email

# グループモデル
class Group(models.Model):
    # UUIDフィールドはグループの一意識別子
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    # グループ名フィールド
    name = models.CharField(max_length=255, null=False)
    # グループ作成者の外部キー、ユーザーモデルと関連付け
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    # グループ作成日時、自動的に現在の日時が設定される
    created_at = models.DateTimeField(auto_now_add=True)
    # 最終更新日時、更新されるたびに現在の日時が設定される
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# グループメンバーモデル
class GroupMember(models.Model):
    # UUIDフィールドはグループメンバーの一意識別子
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    # グループの外部キー、グループモデルと関連付け
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')
    # ユーザーの外部キー、ユーザーモデルと関連付け（1対1の関係を反映）
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='group')
    # 参加日時、自動的に現在の日時が設定される
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.email} in {self.group.name}'

    # groupとuserの組み合わせが一意であることを保証
    class Meta:
        unique_together = ('group', 'user')
