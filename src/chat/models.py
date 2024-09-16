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
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    # メッセージの内容
    content = models.TextField()
    # メッセージの送信日時
    timestamp = models.DateTimeField(auto_now_add=True)

    # オブジェクトの文字列表現
    def __str__(self):
        return f"Message from {self.sender.username} in {self.group.id} at {self.timestamp}"
from accounts.models import CustomUser

class SleepAdvice(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    sleep_time = models.TimeField()  # 睡眠開始時間データを保存
    wake_time = models.TimeField()   # 起床時刻データを保存
    pre_sleep_activities = models.TextField()    # 例: "テレビを見た"
    advice = models.TextField()                  # 睡眠AIのアドバイス
    created_at = models.DateTimeField(auto_now_add=True)  # 保存日時

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"
