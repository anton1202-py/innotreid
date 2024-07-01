from django.urls import path

from . import views

urlpatterns = [

    path('ozon_ad_campaigns', views.ozon_ad_campaigns,
         name='ozon_ad_campaigns'),
]
