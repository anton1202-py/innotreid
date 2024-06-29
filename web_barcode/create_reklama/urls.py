from django.urls import path

from . import views

urlpatterns = [
    path('create_reklama_create_campaign', views.create_campaign,
         name='create_reklama_create_campaign'),
    path('create_reklama_create_many_campaigns', views.create_many_campaigns,
         name='create_reklama_create_many_campaigns'),
    path('campaigns_list', views.campaigns_were_created_with_system,
         name='campaigns_list'),
    path('common_minus_words', views.common_minus_words,
         name='common_minus_words'),


    path('update_common_minus_words', views.update_common_minus_words,
         name='update_common_minus_words'),
    path('start_checked_campaigns', views.start_checked_campaigns,
         name='start_checked_campaigns'),
    path('change_percent_for_advert', views.change_percent_for_advert,
         name='change_percent_for_advert'),
]
