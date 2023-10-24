from django.urls import path

from . import views

urlpatterns = [
     path('task_creation', views.task_creation, name='task_creation'),
     #path('delivery_data', views.product_detail, name='delivery_data'),
     #path('task/<int:pk>',
     #     views.ProductTaskDetailView.as_view(),
     #     name='delivery_data'
     #     ),
     path('task/<int:task_id>',
          views.product_detail,
          name='delivery_data'
          ),
]