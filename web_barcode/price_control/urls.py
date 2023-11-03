from django.urls import path

from . import views

urlpatterns = [
    path('add_article', views.add_article, name='add_article'),
    path('<str:wb_article>',
         views.DataForAnalysisDetailView.as_view(),
         name='price_article_detail'
         ),
]
