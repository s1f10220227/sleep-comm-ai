from django.urls import path
from . import views

urlpatterns = [
    path('progress_check/', views.progress_check, name='progress_check'),
]
