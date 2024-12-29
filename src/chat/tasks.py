from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Group, Message
from accounts.models import CustomUser
import openai  # OpenAIライブラリを使用
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# settings.pyで定義した環境変数OPENAI_API_KEY, OPENAI_API_BASEを参照する
OPENAI_API_KEY = settings.OPENAI_API_KEY
OPENAI_API_BASE = settings.OPENAI_API_BASE

# AIモデルの初期化
chat = openai.ChatCompletion


@shared_task
def send_daily_message():
    try:
        channel_layer = get_channel_layer()
        groups = Group.objects.all()

        message = "http://127.0.0.1:8080/chat/sleep_q/"

        ai_user = CustomUser.objects.get(username='AI Assistant')

        for group in groups:
            room_group_name = f'chat_{group.id}'

            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': 'AI Assistant'
                }
            )

            Message.objects.create(sender=ai_user, group=group, content=message)

        logger.info("Daily message sent successfully")
        return "Daily message sent successfully"

    except Exception as e:
        logger.error(f"Error sending daily message: {str(e)}")
        return f"Error sending daily message: {str(e)}"


@shared_task
def send_daily_tips():
    try:
        input_message = "睡眠の質を高めるための簡単なTipsや雑学などを教えてください。50字以内でお願いします。"
        response = chat.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a sleep expert who provides advice on healthy sleep habits."},
                {"role": "user", "content": input_message}
            ],
            api_key=OPENAI_API_KEY,
            api_base=OPENAI_API_BASE,
            temperature=0.7,
        )
        ai_response = response['choices'][0]['message']['content'].strip()
        message = "今日の睡眠豆知識\n" + ai_response if ai_response else "睡眠に関するTipsを取得できませんでした。"

        ai_user = CustomUser.objects.get(username='AI Assistant')
        groups = Group.objects.all()
        channel_layer = get_channel_layer()

        for group in groups:
            room_group_name = f'chat_{group.id}'

            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': 'AI Assistant'
                }
            )

            Message.objects.create(sender=ai_user, group=group, content=message)

        logger.info("Daily sleep tips sent successfully")
        return "Daily sleep tips sent successfully"

    except Exception as e:
        logger.error(f"Error sending daily tips: {str(e)}")
        return f"Error sending daily tips: {str(e)}"
