from django.contrib import admin
from .models import SleepAdvice, Message, Mission

admin.site.register(SleepAdvice)
admin.site.register(Message)
admin.site.register(Mission)