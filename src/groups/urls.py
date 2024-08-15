from django.urls import path
from . import views

urlpatterns = [
    path('group_menu/', views.group_menu, name='group_menu'),
    path('group_management/', views.group_management, name='group_management'),
]
