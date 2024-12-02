from django.urls import path
from . import views

urlpatterns = [
    path('group/<uuid:group_id>/', views.room, name='room'),
    path('feedback_chat/', views.feedback_chat, name='feedback_chat'),
    path('chat/<uuid:group_id>/create_missions/', views.create_missions, name='create_missions'),
    path('chat/<uuid:group_id>/confirm_mission/', views.confirm_mission, name='confirm_mission'),
    path('chat/<uuid:group_id>/vote_mission/', views.vote_mission, name='vote_mission'),
]
