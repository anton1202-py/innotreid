from django.urls import path

from . import views

urlpatterns = [
    path('article_compare', views.article_compare,
         name='price_system_article_compare'),
]
