from django.urls import path

from . import views

urlpatterns = [
    path('create_reklama_create_campaign', views.create_campaign,
         name='create_reklama_create_campaign'),
    path('create_reklama_create_many_campaigns', views.create_many_campaigns,
         name='create_reklama_create_many_campaigns'),
]