from django.urls import path

from . import views

urlpatterns = [
     path('delivery_number', views.product_detail, name='delivery_number'),
     path('delivery_data', views.product_detail, name='delivery_data'),
]