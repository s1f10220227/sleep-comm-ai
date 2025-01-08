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
        'schedule': crontab(hour=7, minute=0), # 7:00 JST
    },
    # グループ睡眠分析を送信
    'send-group-sleep-analysis': {
        'task': 'chat.tasks.send_group_sleep_analysis',
        'schedule': crontab(hour=15, minute=0),  # 15:00 JST
    },
    # 睡眠豆知識を送信
    'send-sleep-tips': {
        'task': 'chat.tasks.send_sleep_tips',
        'schedule': crontab(hour=18, minute=0), # 18:00 JST
    },
    # 3日間の睡眠分析を送信
    'send-three-day-sleep-analysis': {
        'task': 'chat.tasks.send_three_day_sleep_analysis',
        'schedule': crontab(hour=15, minute=0),  # 15:00 JST
    },
    # グループを解散
    'disband-groups': {
        'task': 'chat.tasks.disband_groups',
        'schedule': crontab(hour=23, minute=59),  # 23:59 JST
    },
}

app.conf.timezone = 'Asia/Tokyo'
