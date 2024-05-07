from django.urls import path

from . import views

urlpatterns = [
    path('celery_tasks_view', views.celery_tasks_view,
         name='celery_tasks_view'),
    path('long_running_function/', views.long_running_function_view,
         name='long_running_function'),
]
