from django.urls import path

from . import views

urlpatterns = [
    path('feedbacks_articles_list_info', views.articles_list_with_main_info,
         name='feedbacks_articles_list_info'),

    path('feedbacks_article_feedbacks/<str:common_article>',
         views.FeedbacksArticleDetailView.as_view(),
         name='feedbacks_article_feedbacks'
         ),

    # ========== JQUERY поля ===========#
    # path('update_model_field/', views.update_model_field,
    #      name='update_model_field'),
    # path('update_article_designer_boolean_field/', views.update_article_designer_boolean_field,
    #      name='update_article_designer_boolean_field'),
    # path('update_article_copyright_boolean_field/', views.update_article_copyright_boolean_field,
    #      name='update_article_copyright_boolean_field'),
    # path('filter_get_delete_request/', views.filter_get_delete_request,
    #      name='filter_get_delete_request'),
    # path('update_percent_reward/', views.update_percent_reward,
    #      name='update_percent_reward'),
    # path('designer_rewards_download_excel/', views.download_designer_rewards_excel,
    #      name='designer_rewards_download_excel'),
    # path('designer_sales_download_excel/', views.download_designer_sales_excel,
    #      name='designer_sales_download_excel'),
]
