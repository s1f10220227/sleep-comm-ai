from django.urls import path
from . import views

urlpatterns = [
    path('results_and_feedback/', views.results_and_feedback, name='results_and_feedback'),
]
