from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
    path('signup/', views.signup, name='signup'),  # サインアップ用のURLを追加
    path('logout/', views.logout_view, name='logout'),
]
