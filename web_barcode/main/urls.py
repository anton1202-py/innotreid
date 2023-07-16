from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='home'),
    path('barcode', views.barcode, name='barcode'),
    path('qrcode', views.qrcode, name='qrcode'),
    path('barcodebox', views.barcodebox, name='barcodebox'),
]
