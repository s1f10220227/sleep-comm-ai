import uuid
from django.db import models
from groups.models import Group
from accounts.models import CustomUser

# メッセージモデル
class Message(models.Model):
    # UUIDをプライマリキーとして使用
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # メッセージの送信者
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    # メッセージが属するグループ
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    # メッセージの内容
    content = models.TextField()
    # メッセージの送信日時
    timestamp = models.DateTimeField(auto_now_add=True)

    # オブジェクトの文字列表現
    def __str__(self):
        return f"Message from {self.sender.username} in {self.group.id} at {self.timestamp}"
