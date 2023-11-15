import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web_barcode.settings")
# app = Celery("web_barcode")
app = Celery('ozon_system.tasks', broker='redis://localhost:6379/0')
# app.config_from_object("web_barcode.celeryconfig", namespace="CELERY")
app.autodiscover_tasks()
