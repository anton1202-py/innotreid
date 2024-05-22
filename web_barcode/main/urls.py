from database import views
from django.urls import path

from .views import user_groups

urlpatterns = [
    path('', views.database_home, name='database_home'),
    path('', user_groups, name='user_groups'),

]
