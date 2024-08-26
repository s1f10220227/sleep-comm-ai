import uuid
from django.db import models
from django.contrib.auth.models import User

# グループモデル
class Group(models.Model):
    # UUIDをプライマリキーとして使用
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # グループがプライベートかどうかを示すフラグ
    is_private = models.BooleanField(default=False)
    # 招待コード（プライベートグループの場合に使用）
    invite_code = models.CharField(max_length=100, null=True, blank=True)

# グループメンバーモデル
class GroupMember(models.Model):
    # UUIDをプライマリキーとして使用
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # グループへの外部キー
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    # ユーザーへの外部キー
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # オブジェクトの文字列表現
    def __str__(self):
        return f"{self.user.username} in {self.group.name}"

