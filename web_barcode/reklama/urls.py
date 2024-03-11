from django.urls import path

from . import views

urlpatterns = [
    path('ad_campaigns', views.ad_campaign_add,
         name='ad_campaigns'),
]