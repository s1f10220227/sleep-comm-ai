from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Group, Message
from accounts.models import CustomUser
import logging

logger = logging.getLogger(__name__)

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
