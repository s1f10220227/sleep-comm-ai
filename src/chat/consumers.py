import os
import json
import openai  # OpenAIライブラリを使用
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Message
from groups.models import Group
from accounts.models import CustomUser
from django.contrib.auth import get_user_model

# ログ設定
logging.basicConfig(filename='debug.log', level=logging.DEBUG)

# APIキーとベースURLを設定
OPENAI_API_KEY = ''  # YOUR_API_KEY
OPENAI_API_BASE = 'https://api.openai.iniad.org/api/v1'

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.room_group_name = f'chat_{self.group_id}'

        logging.debug(f"Connecting to group: {self.room_group_name}")

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logging.debug(f"Disconnected from group: {self.room_group_name}")

    async def receive(self, text_data):
        logging.debug(f"Received message: {text_data}")

        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = text_data_json['username']

        # Save user message to database
        await self.save_message(username, message)
        logging.debug(f"Message saved to database by {username}")

        # Send user message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username
            }
        )

        # Check for triggering AI response
        if "@AI" in message:
            ai_content = await self.generate_ai_response(message)
            logging.debug(f"AI response generated: {ai_content}")

            # Save and send AI message
            await self.send_ai_message(ai_content)
            logging.debug(f"AI message process completed for: {ai_content}")

    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        logging.debug(f"Broadcasting message from {username}: {message}")

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username
        }))

    @sync_to_async
    def save_message(self, username, message):
        user = CustomUser.objects.get(username=username)
        group = Group.objects.get(id=self.group_id)
        Message.objects.create(sender=user, group=group, content=message)

    @sync_to_async
    def send_ai_message(self, content):
        try:
            User = get_user_model()
            ai_user, _ = User.objects.get_or_create(username='AI Assistant')
            group = Group.objects.get(id=self.group_id)

            logging.debug(f"Saving AI message: {content} by {ai_user.username}")

            # メッセージを保存
            msg_instance = Message.objects.create(sender=ai_user, group=group, content=content)
        
            logging.debug(f"AI message saved: {msg_instance.id}")

            # AIのメッセージを送信
            self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': content,
                    'username': 'AI Assistant'
                }
            )
        except Exception as e:
            logging.error(f"Error saving AI message: {str(e)}")

    async def generate_ai_response(self, user_message):
        # OpenAI APIでアドバイスを取得
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a sleep expert who provides advice on healthy sleep habits."},
                    {"role": "user", "content": (
                        f"以下はユーザーからの質問です。: {user_message} "
                        "この質問に簡潔に答えて。できれば3行くらい"
                    )}
                ],
                api_key=OPENAI_API_KEY,
                api_base=OPENAI_API_BASE
            )


            # APIからのレスポンスを抽出
            ai_message_content = response.choices[0].message['content'].strip()
            logging.debug(f"AI API response: {ai_message_content}")
            return ai_message_content

        except Exception as e:
            logging.error(f"Error in generate_ai_response: {str(e)}")
            return "AIによる応答生成に失敗しました。もう一度お試しください。"