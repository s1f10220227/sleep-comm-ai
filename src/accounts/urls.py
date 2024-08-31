from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_signup, name='login_signup'),
    path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
    path('profile/', views.profile, name='profile'),
    path('signup/', views.signup, name='signup'),  # サインアップ用のURLを追加
]
