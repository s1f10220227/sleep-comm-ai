from django.urls import path
from . import views

urlpatterns = [
    path('group/<uuid:group_id>/', views.room, name='room'),
]
