import datetime
import json
import logging
import os
from collections import Counter
from datetime import datetime

import pandas as pd
import requests
from celery import Celery, shared_task
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from dotenv import load_dotenv

from .models import ArticleAmountRating

# from web_barcode.celery import app


load_dotenv()

logger = logging.getLogger(__name__)

app = Celery('myapp', broker='redis://localhost:6379/0')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task
def my_task(compaign_id):
    from .views import access_token
    logger.info("Функция my_task приняла задание для compaign_id %s в %s",
                compaign_id, datetime.now())
    print('Начало работы')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token()}',
    }
    url = f"https://performance.ozon.ru:443/api/client/campaign/{compaign_id}/deactivate"
    payload_deactive = json.dumps({
        "campaignId": compaign_id
    })
    response = requests.request(
        "POST", url, headers=headers, data=payload_deactive)
    print("Функция выполняется в", datetime.now())
