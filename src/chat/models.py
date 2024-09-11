import uuid
from django.db import models
from accounts.models import CustomUser
from groups.models import Group

# チャットルームモデル
class ChatRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # プライマリキーとしてUUIDを使用
    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL)  # グループに関連付け（NULL許可）
    is_private = models.BooleanField(default=False)  # プライベートチャットかどうか

    def __str__(self):
        return f"ChatRoom ({self.group})" if self.group else "Private ChatRoom"

# メッセージモデル
class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # プライマリキーとしてUUIDを使用
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)  # チャットルームに関連付け
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # ユーザーに関連付け
    content = models.TextField()  # メッセージの内容
    created_at = models.DateTimeField(auto_now_add=True)  # 作成日時（自動設定）

    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}"

# 添付ファイルモデル
class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # プライマリキーとしてUUIDを使用
    message = models.ForeignKey(Message, related_name='attachments', on_delete=models.CASCADE)  # メッセージに関連付け
    file = models.FileField(upload_to='attachments/')  # 添付ファイル

    def __str__(self):
        return f"Attachment for {self.message.id}"

# リアクションモデル
class Reaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # プライマリキーとしてUUIDを使用
    message = models.ForeignKey(Message, related_name='reactions', on_delete=models.CASCADE)  # メッセージに関連付け
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # ユーザーに関連付け
    reaction_type = models.CharField(max_length=20)  # リアクションのタイプ（例：いいね、ハートなど）

    def __str__(self):
        return f"{self.user.username} reacted with {self.reaction_type}"

# 未読メッセージモデル
class UnreadMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # プライマリキーとしてUUIDを使用
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # ユーザーに関連付け
    message = models.ForeignKey(Message, on_delete=models.CASCADE)  # メッセージに関連付け

    def __str__(self):
        return f"Unread message for {self.user.username}: {self.message.id}"
