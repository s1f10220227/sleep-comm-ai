from django.urls import path
from . import views

urlpatterns = [
    path('group/<uuid:group_id>/', views.room, name='room'),
    path('feedback_chat/', views.feedback_chat, name='feedback_chat'),
    path('chat/<uuid:group_id>/create_mission/', views.create_mission, name='create_mission'),
]
