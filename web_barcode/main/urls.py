from django.urls import path

from database import views


urlpatterns = [
    path('', views.database_home, name='database_home'),

]
