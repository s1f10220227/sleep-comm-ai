from django.contrib import admin
from django.urls import path
from main import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_signup, name='login_signup'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('main_menu/', views.main_menu, name='main_menu'),
    path('group_management/', views.group_management, name='group_management'),
    path('profile/', views.profile, name='profile'),
    path('chat/', views.group_chat, name='group_chat'),
    path('questions/', views.answer_questions, name='answer_questions'),
    path('progress/', views.progress_check, name='progress_check'),
    path('results/', views.results_feedback, name='results_feedback'),
]
