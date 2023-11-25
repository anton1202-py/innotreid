from django.urls import path

from . import views

urlpatterns = [
    path('ozon_system_main_data', views.ozon_main_info_table,
         name='ozon_system_main_data'),
    path('ozon_adv_group', views.ozon_adv_group,
         name='ozon_adv_group'),
    path('campaign_articles/<int:campaign_id>', views.ozon_campaing_article_info,
         name='ozon_campaing_article_info'),
    path('ozon_compaign_timetable', views.group_adv_compaign_timetable,
         name='ozon_campaing_timetable'),
]
