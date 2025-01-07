import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # 睡眠アンケートを送信
    'send-sleep-questionnaire': {
        'task': 'chat.tasks.send_sleep_questionnaire',
        'schedule': crontab(hour=7, minute=00), # 7:00 JST
    },
    # グループ睡眠分析を送信
    'send-group-sleep-analysis': {
        'task': 'chat.tasks.send_group_sleep_analysis',
        'schedule': crontab(hour=15, minute=00),  # 15:00 JST
    },
    'send-mission-related-tips': {
        'task': 'chat.tasks.send_mission_related_tips',
        'schedule': crontab(hour=18, minute=00), # 18:00 JST
    },
    'send-mission-complete-message': {
        'task': 'chat.tasks.send_mission_complete_message',
        'schedule': crontab(hour=15, minute=00),  # 15:00 JST
    },
    'check-and-disband-groups': {
        'task': 'chat.tasks.check_and_disband_groups',
        'schedule': crontab(hour=0, minute=0),  # 0:00 JST
    },
}

app.conf.timezone = 'Asia/Tokyo'
