from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Group, Message, Mission
from accounts.models import CustomUser
from django.utils import timezone
from django.utils.timezone import localtime
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_daily_message():
    try:
        channel_layer = get_channel_layer()
        groups = Group.objects.all()
        message = "http://127.0.0.1:8080/chat/feedback_chat/"
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
                days_since_creation = (localtime(timezone.now()).date() - localtime(latest_mission.created_at).date()).days

                if days_since_creation == 2:  # ミッション作成から2日経過
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
