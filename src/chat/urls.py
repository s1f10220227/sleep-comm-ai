from django.urls import path
from . import views

urlpatterns = [
    path('feedback_chat/', views.feedback_chat, name='feedback_chat'),
]
