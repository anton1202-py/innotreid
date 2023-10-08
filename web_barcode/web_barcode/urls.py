from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('database/', include('database.urls')),
    path('database_ya/', include('database_yandex.urls')),
    path('production/', include('production.urls')),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
