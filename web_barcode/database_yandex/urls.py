from django.urls import path

from . import views

urlpatterns = [
     path('innotreid_stock_yandex', views.database_yandex_stock, name='innotreid_stock_yandex'),
]
