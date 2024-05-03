from django.urls import path

from . import views

urlpatterns = [
    path('motivation_article_designers', views.article_designers,
         name='motivation_article_designers'),
    path('update_model_field/', views.update_model_field,
         name='update_model_field'),
    path('motivation_article_sale', views.article_sale,
         name='motivation_article_sale'),
    path('motivation_designers_rewards', views.designers_rewards,
         name='motivation_designers_rewards'),
]
