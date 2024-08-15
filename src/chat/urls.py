from django.urls import path
from . import views

urlpatterns = [
    path('group_chat/', views.group_chat, name='group_chat'),
]
