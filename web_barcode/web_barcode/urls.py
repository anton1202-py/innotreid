from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('database/', include('database.urls')),
    path('database_ya/', include('database_yandex.urls')),
    path('production/', include('production.urls')),
    path('price_control/', include('price_control.urls')),
    path('ozon_system/', include('ozon_system.urls')),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
