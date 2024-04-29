from django.urls import path

from . import views

urlpatterns = [
    path('motivation_article_designers', views.article_designers,
         name='motivation_article_designers'),
    path('motivation_article_sale', views.article_sale,
         name='motivation_article_sale'),
    path('motivation_designers_rewards', views.designers_rewards,
         name='motivation_designers_rewards'),
]
