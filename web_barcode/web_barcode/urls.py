from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('database/', include('database.urls')),
    path('database_ya/', include('database_yandex.urls')),
    path('feedbacks/', include('feedbacks.urls')),
    path('production/', include('production.urls')),
    path('price_control/', include('price_control.urls')),
    path('ozon_system/', include('ozon_system.urls')),
    path('price_system/', include('price_system.urls')),
    path('reklama/', include('reklama.urls')),
    path('celery_view/', include('celery_view.urls')),
    path('motivation/', include('motivation.urls')),
    path('analytika_reklama/', include('analytika_reklama.urls')),
    path('create_reklama/', include('create_reklama.urls')),
    path('actions/', include('actions.urls')),


] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
