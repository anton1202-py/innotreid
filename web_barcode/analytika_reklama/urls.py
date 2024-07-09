from django.urls import path

from . import views

urlpatterns = [
    path('reklama_data_info', views.main_adv_info,
         name='reklama_data_info'),
    path('common_adv_statistic', views.common_adv_statistic,
         name='common_adv_statistic'),

    path('adv_kw_statistic', views.keyword_statistic_info,
         name='adv_kw_statistic'),

    path('adv_article_words_info',
         views.articles_words_main_info,
         name='adv_article_words_info'
         ),
    path('adv_campaign_clusters/<int:id>',
         views.CampaignClustersView.as_view(),
         name='adv_campaign_clusters'
         ),
    path('adv_campaign_daily_statistic/<int:id>',
         views.CampaignDailyStatisticView.as_view(),
         name='adv_campaign_daily_statistic'
         ),
    path('adv_article_clusters/<int:id>',
         views.ArticleClustersView.as_view(),
         name='adv_article_clusters'
         ),
    path('adv_article_excluded/<int:id>',
         views.MainArticleExcludedView.as_view(),
         name='adv_article_excluded'
         ),
    path('adv_keyphrase_article_statistic/<int:id>',
         views.KeyPhraseCampaignStatisticView.as_view(),
         name='adv_keyphrase_article_statistic'
         ),
]
