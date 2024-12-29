import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send-daily-message': {
        'task': 'chat.tasks.send_daily_message',
        'schedule': crontab(hour=11, minute=32), # ex. 13:15 JST
    },
    'send-daily-tips': {
        'task': 'chat.tasks.send_daily_tips',
        'schedule': crontab(hour=11, minute=32), # ex. 13:15 JST
    },
}

app.conf.timezone = 'Asia/Tokyo'
