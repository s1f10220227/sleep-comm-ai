from django.db import models
from accounts.models import CustomUser

class SleepAdvice(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    sleep_time = models.TimeField()  # 睡眠開始時間データを保存
    wake_time = models.TimeField()   # 起床時刻データを保存 
    pre_sleep_activities = models.TextField()    # 例: "テレビを見た"
    advice = models.TextField()                 # 睡眠AIのアドバイス
    topic_question = models.TextField(null=True)         #グループ参加前限定質問の回答
    created_at = models.DateTimeField(auto_now_add=True)  # 保存日時


    def __str__(self):
        return f"{self.user.username} - {self.created_at}"