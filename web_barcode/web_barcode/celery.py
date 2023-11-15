import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web_barcode.settings")
# app = Celery("web_barcode")
app = Celery('ozon_system',
             include=['ozon_system.tasks'])
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
