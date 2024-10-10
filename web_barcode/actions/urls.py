from django.urls import path

from . import views

urlpatterns = [
    path('actions_compare_data', views.actions_compare_data,
         name='actions_compare_data'),
    path('article_in_actions', views.article_in_actions,
        name='article_in_actions'),
        
    # ========== ДЛЯ AJAX ЗАПРОСОВ ========= #
    path('get-actions', views.get_actions, name='get_actions'),
    path('add_to_action', views.add_to_action, name='add_to_action'),
]
