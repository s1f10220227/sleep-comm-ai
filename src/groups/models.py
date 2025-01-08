import uuid
from django.db import models
from django.core.exceptions import ValidationError
from accounts.models import CustomUser

# グループモデル
class Group(models.Model):
    # UUIDをプライマリキーとして使用
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # グループがプライベートかどうかを示すフラグ
    is_private = models.BooleanField(default=False)
    # 招待コード（プライベートグループの場合に使用）
    invite_code = models.CharField(max_length=100, null=True, blank=True)
    # 締切時刻を保存するフィールド
    vote_deadline = models.DateTimeField(null=True, blank=True)
    # 初期メッセージを送信したかどうかを示すフラグ
    init_message_sent = models.BooleanField(default=False)
    # 参加締め切りのフラグ
    is_join_closed = models.BooleanField(default=False) 

# グループメンバーモデル
class GroupMember(models.Model):
    # UUIDをプライマリキーとして使用
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # グループへの外部キー
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')
    # ユーザーへの外部キー
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if self.group.members.count() >= 6:
            raise ValidationError("このグループは既に満員です。")
        super().save(*args, **kwargs)
    # オブジェクトの文字列表現
    def __str__(self):
        return f"{self.user.username} in {self.group.id}"
