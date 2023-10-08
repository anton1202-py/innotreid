from django.urls import path

from . import views

urlpatterns = [
     path('delivery_number', views.delivery_number, name='delivery_number'),
]