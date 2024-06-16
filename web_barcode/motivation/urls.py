from django.urls import path

from . import views

urlpatterns = [
    path('motivation_article_type', views.article_type,
         name='motivation_article_type'),
    path('motivation_percent_rewards', views.percent_designers_rewards,
         name='motivation_percent_rewards'),
    path('motivation_article_designers', views.article_designers,
         name='motivation_article_designers'),
    path('motivation_designers_rewards', views.designers_rewards,
         name='motivation_designers_rewards'),
    path('motivation_designers_sale/<int:pk>',
         views.MotivationDesignersSaleDetailView.as_view(),
         name='motivation_designers_sale_detail'
         ),
    path('motivation_designers_reward/<int:pk>',
         views.MotivationDesignersRewardDetailView.as_view(),
         name='motivation_designers_rewards_detail'
         ),

    # ========== JQUERY поля ===========#
    path('update_model_field/', views.update_model_field,
         name='update_model_field'),
    path('update_article_designer_boolean_field/', views.update_article_designer_boolean_field,
         name='update_article_designer_boolean_field'),
    path('update_article_copyright_boolean_field/', views.update_article_copyright_boolean_field,
         name='update_article_copyright_boolean_field'),
    path('filter_get_delete_request/', views.filter_get_delete_request,
         name='filter_get_delete_request'),
    path('update_percent_reward/', views.update_percent_reward,
         name='update_percent_reward'),
    path('designer_rewards_download_excel/', views.download_designer_rewards_excel,
         name='designer_rewards_download_excel'),
]
