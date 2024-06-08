from django.urls import path

from . import views

urlpatterns = [
    path('reklama_data_info', views.main_adv_info,
         name='reklama_data_info'),
    path('common_adv_statistic', views.common_adv_statistic,
         name='common_adv_statistic'),

    path('adv_campaign_clusters/<int:id>',
         views.CampaignClustersView.as_view(),
         name='adv_campaign_clusters'
         ),
    path('adv_campaign_daily_statistic/<int:id>',
         views.CampaignDailyStatisticView.as_view(),
         name='adv_campaign_daily_statistic'
         ),
]
