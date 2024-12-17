import uuid
from django.db import models
from groups.models import Group
from accounts.models import CustomUser
from django.utils import timezone
from datetime import datetime, date, timedelta

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

class SleepAdvice(models.Model):
    SLEEP_QUALITY_CHOICES = [
        (1, '目覚めが悪かった'),
        (2, 'あまり良くなかった'),
        (3, '普通'),
        (4, '良かった'),
        (5, 'すっきり目覚めた'),
    ]

    MISSION_ACHIEVEMENT_CHOICES = [
        (1, '全くできなかった'),
        (2, 'あまりできなかった'),
        (3, '半分くらいできた'),
        (4, 'ほぼできた'),
        (5, '完全にできた'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    sleep_time = models.TimeField()  # 就寝時刻
    wake_time = models.TimeField()   # 起床時刻
    sleep_duration = models.DurationField(null=True)  # 睡眠時間
    sleep_quality = models.IntegerField(choices=SLEEP_QUALITY_CHOICES, null=True)   # 睡眠休養感
    pre_sleep_activities = models.TextField()    # 取り組みたいこと
    advice = models.TextField()                  # 睡眠AIのアドバイス
    topic_question = models.TextField(null=True)  # 寝る前にやったこと
    mission_achievement = models.IntegerField(choices=MISSION_ACHIEVEMENT_CHOICES, null=True)  # ミッション達成度
    created_at = models.DateTimeField(auto_now_add=True)  # 保存日時

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"

    def save(self, *args, **kwargs):
        # 睡眠時間を計算
        sleep_datetime = datetime.combine(date.today(), self.sleep_time)
        wake_datetime = datetime.combine(date.today(), self.wake_time)

        # 起床時刻が就寝時刻より前の場合（深夜をまたぐ場合）
        if wake_datetime < sleep_datetime:
            wake_datetime += timedelta(days=1)

        self.sleep_duration = wake_datetime - sleep_datetime
        super().save(*args, **kwargs)

class Mission(models.Model):
    mission = models.TextField() # ミッションの内容を保存
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    confirmed = models.BooleanField(default=False)  # 確定状態を記録するフィールド
    created_at = models.DateTimeField(auto_now_add=True)

# ミッション案を保持するモデル
class MissionOption(models.Model):
    text = models.CharField(max_length=255)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    votes = models.PositiveIntegerField(default=0)

# ユーザーの投票を管理するモデル
class Vote(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    mission_option = models.ForeignKey(MissionOption, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'group')  # ユーザーごとにグループ内で一度だけ投票可能
