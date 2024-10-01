from django.urls import path

from . import views

urlpatterns = [
    path('actions_compare_data', views.actions_compare_data,
         name='actions_compare_data'),
        
    # ========== ДЛЯ AJAX ЗАПРОСОВ ========= #
    path('get-actions', views.get_actions, name='get_actions'),
]
