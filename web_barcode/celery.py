import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web_barcode.settings")
# app = Celery("web_barcode")
app = Celery('ozon_system',
             include=['ozon_system.tasks', 'ozon_system.my_task'])
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
