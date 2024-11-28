import os
import json
import openai  # OpenAIライブラリを使用
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Message, SleepAdvice
from groups.models import Group
from accounts.models import CustomUser
from django.conf import settings

# settings.pyで定義した環境変数OPENAI_API_KEY, OPENAI_API_BASEを参照する
OPENAI_API_KEY = settings.OPENAI_API_KEY
OPENAI_API_BASE = settings.OPENAI_API_BASE
# ログ設定
logging.basicConfig(filename='debug.log', level=logging.DEBUG)

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
            ai_response = await self.generate_ai_response(message)
            logging.debug(f"AI response generated: {ai_response}")
            await self.save_message('AI Assistant', ai_response)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': ai_response,
                    'username': 'AI Assistant'
                }
            )
            logging.debug(f"AI message process completed for: {ai_response}")

        # Check for triggering AI response
        if "@共有" in message:  # 条件は必要に応じて変更
            advice = await self.get_sleep_advice(username)
            if advice:
                await self.save_message('AI Assistant', advice)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': advice,
                        'username': 'AI Assistant'
                    }
                )

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

    async def generate_ai_response(self, user_message):
        try:
            input=(f"以下の質問に50字程度で簡潔に回答してください。{user_message}。なお、睡眠に関係しない質問であった場合は回答しないでください。")
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "You are a sleep expert who provides advice on healthy sleep habits."},
                        {"role": "user", "content": input}],
                api_key=OPENAI_API_KEY,
                api_base=OPENAI_API_BASE,
                max_tokens=50,
                temperature=0.2,
            )
            ai_response = response['choices'][0]['message']['content'].strip()
            logging.debug(f"AI API response: {ai_response}")
            return ai_response
        except Exception as e:
            logging.error(f"Error in generate_ai_response: {str(e)}")
            return "AIによる応答生成に失敗しました。しばらく待ってからもう一度お試しください。"

    @sync_to_async
    def get_sleep_advice(self, username):
        try:
            user = CustomUser.objects.get(username=username)
            # 最新のSleepAdviceを取得
            advice_entry = SleepAdvice.objects.filter(user=user).latest('created_at')
            advice = f"{user.username}さんのアドバイスです。ぜひ参考にしてください。: {advice_entry.advice}"
            return advice
        except SleepAdvice.DoesNotExist:
            return "このユーザーのアドバイスはまだありません。"