from django.urls import path

from . import views

urlpatterns = [
    path('article_compare', views.article_compare,
         name='price_system_article_compare'),
    path('price_groups', views.groups_view,
         name='price_groups'),
    path('article_groups', views.article_groups_view,
         name='article_groups'),
]
