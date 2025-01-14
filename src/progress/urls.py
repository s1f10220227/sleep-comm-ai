from django.urls import path
from . import views

urlpatterns = [
    path('sleep_data/', views.sleep_data, name='sleep_data'),
]
