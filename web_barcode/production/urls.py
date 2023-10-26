from django.urls import path

from . import views

urlpatterns = [
     path('task_creation', views.task_creation, name='task_creation'),
     path('task/<int:task_id>',
          views.product_detail,
          name='delivery_data'
          ),
]