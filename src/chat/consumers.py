import json
import openai
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Message
from groups.models import Group
from accounts.models import CustomUser
from django.conf import settings

# settings.pyで定義した環境変数OPENAI_API_KEY, OPENAI_API_BASEを参照する
OPENAI_API_KEY = settings.OPENAI_API_KEY 
OPENAI_API_BASE = settings.OPENAI_API_BASE

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.room_group_name = f'chat_{self.group_id}'

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

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = text_data_json['username']

        # Save message to database
        await self.save_message(username, message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username
            }
        )

        if "@AI" in message:
            ai_response = await self.generate_ai_response(message) 
            await self.save_message('AI Assistant', ai_response) 
            await self.channel_layer.group_send( 
                self.room_group_name, 
                { 
                    'type': 'chat_message', 
                    'message': ai_response, 
                    'username': 'AI Assistant' 
                } 
            )

    async def chat_message(self, event):
        message = event['message']
        username = event['username']

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
            return ai_response
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return "AIによる応答生成に失敗しました。しばらく待ってからもう一度お試しください。"
