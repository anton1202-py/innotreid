from django.urls import path

from . import views

urlpatterns = [
    path('celery_tasks_view', views.celery_tasks_view,
         name='celery_tasks_view'),
]
