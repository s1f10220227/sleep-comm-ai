import logging

from django.conf import settings
from django.utils import timezone
from django.utils.timezone import localtime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from celery import shared_task

import openai

from .models import Group, Message, Mission
from accounts.models import CustomUser

logger = logging.getLogger(__name__)

# settings.pyで定義した環境変数OPENAI_API_KEY, OPENAI_API_BASEを参照する
OPENAI_API_KEY = settings.OPENAI_API_KEY
OPENAI_API_BASE = settings.OPENAI_API_BASE

# AIモデルの初期化
chat = openai.ChatCompletion

@shared_task
def send_init_message(group_id):
    try:
        channel_layer = get_channel_layer()
        group = Group.objects.get(id=group_id)
        room_group_name = f'chat_{group.id}'
        ai_user = CustomUser.objects.get(username='AI Assistant')
        message = (
            "グループへようこそ！私はAIアシスタントです。\n"
            "このグループでは、メンバーの皆さんと一緒に目標達成を目指していきます。\n"
        )

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
            'type': 'chat_message',
            'message': message,
            'username': 'AI Assistant'
            }
        )

        Message.objects.create(
            sender=ai_user,
            group=group,
            content=message
        )

        logger.info(f"Initial messages sent successfully to group {group_id}")
        return "Initial messages sent successfully"

    except Exception as e:
        logger.error(f"Error sending initial messages to group {group_id}: {str(e)}")
        return f"Error sending initial messages: {str(e)}"

@shared_task
def send_mission_explanation(group_id, mission_text):
    try:
        # OpenAI APIでミッションの効果説明を生成
        prompt = (
            f"以下のミッションが睡眠にどのように良い影響を与えるか、その理由と効果を100文字程度で説明してください：\n"
            f"ミッション：{mission_text}\n"
            f"※専門的な説明を避け、わかりやすく具体的に説明してください。"
        )

        response = chat.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a sleep expert who explains the benefits of sleep-related activities."},
                {"role": "user", "content": prompt}
            ],
            api_key=OPENAI_API_KEY,
            api_base=OPENAI_API_BASE
        )

        benefits_explanation = response['choices'][0]['message']['content'].strip()

        # 通知メッセージを作成
        notification_message = (
            f"🎯 新しいミッションが確定されました！『{mission_text}』\n\n"
            f"✨ このミッションの効果：\n"
            f"{benefits_explanation}\n\n"
            f"📋 明日朝7時に、睡眠状況とミッションの達成度についてのアンケートが送信されます。"
            f"皆さんの回答をお待ちしています！"
        )

        # グループにメッセージを送信
        group = Group.objects.get(id=group_id)
        ai_user = CustomUser.objects.get(username='AI Assistant')

        # メッセージを作成して保存
        Message.objects.create(
            sender=ai_user,
            group=group,
            content=notification_message
        )

        # ebSocketを通じて送信
        channel_layer = get_channel_layer()
        room_group_name = f'chat_{group_id}'

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'chat_message',
                'message': notification_message,
                'username': 'AI Assistant'
            }
        )

        logger.info(f"Mission explanation sent successfully for group {group_id}")
        return "Mission explanation sent successfully"

    except Exception as e:
        logger.error(f"Error sending mission explanation: {str(e)}")
        return f"Error sending mission explanation: {str(e)}"

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

@shared_task
def send_mission_complete_message():
    try:
        channel_layer = get_channel_layer()
        groups = Group.objects.all()
        message = "ミッション達成おめでとうございます"
        ai_user = CustomUser.objects.get(username='AI Assistant')

        for group in groups:
            # 最新のミッションを取得
            latest_mission = Mission.objects.filter(group=group).order_by('-created_at').first()

            if latest_mission:
                days_since_creation = (localtime(timezone.now()).date() - localtime(latest_mission.created_at).date()).days + 1

                if days_since_creation == 2:  # ミッション作成から3日経過
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

        logger.info("Mission complete messages sent successfully")
        return "Mission complete messages sent successfully"

    except Exception as e:
        logger.error(f"Error sending mission complete messages: {str(e)}")
        return f"Error sending mission complete messages: {str(e)}"
