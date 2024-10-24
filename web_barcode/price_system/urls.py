from django.urls import path

from . import views

urlpatterns = [
    path('article_compare_ip', views.ip_article_compare,
         name='price_system_article_compare_ip'),
    path('article_compare_ooo', views.ooo_article_compare,
         name='price_system_article_compare_ooo'),
    path('article_compare_gramoty', views.gramoty_article_compare,
         name='price_system_article_compare_gramoty'),
    path('delete_articles', views.delete_artices,
         name='delete_articles'),

    path('article_compare/<ur_lico>/<int:pk>',
         views.ArticleCompareDetailKaravaev.as_view(),
         name='article_compare_detail'
         ),
    path('article_compare/<ur_lico>/<int:pk>',
         views.ArticleCompareDetailInnotreid.as_view(),
         name='article_compare_detail'
         ),
    path('article_compare/<ur_lico>/<int:pk>',
         views.ArticleCompareDetailChudes.as_view(),
         name='article_compare_detail'
         ),

    path('price_groups_ip', views.ip_groups_view,
         name='price_groups_ip'),
    path('price_groups_ooo', views.ooo_groups_view,
         name='price_groups_ooo'),
    path('price_groups_gramoty', views.gramoty_groups_view,
         name='price_groups_gramoty'),

    path('article_groups_ip', views.ip_article_groups_view,
         name='article_groups_ip'),
    path('article_groups_ooo', views.ooo_article_groups_view,
         name='article_groups_ooo'),
    path('article_groups_gramoty', views.gramoty_article_groups_view,
         name='article_groups_gramoty'),

    path('article_price_statistic_ip', views.ip_article_price_statistic,
         name='article_price_statistic_ip'),
    path('article_price_statistic_ooo', views.ooo_article_price_statistic,
         name='article_price_statistic_ooo'),
    path('article_price_statistic_gramoty', views.gramoty_article_price_statistic,
         name='article_price_statistic_gramoty'),
]
