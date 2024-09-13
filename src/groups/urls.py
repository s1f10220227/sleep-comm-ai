from django.urls import path
from .views import group_menu, group_management, group_create, group_join

urlpatterns = [
    # HTMLテンプレートをレンダリングするビューのルートを追加
    path('group-menu/', group_menu, name='group_menu'),
    path('group-management/', group_management, name='group_management'),
    path('group-create/', group_create, name='group_create'),
    path('group-join/', group_join, name='group_join'),
]
