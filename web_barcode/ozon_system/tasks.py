import datetime
import json
import os
from collections import Counter
from datetime import datetime

import pandas as pd
import requests
from celery import shared_task
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from dotenv import load_dotenv

from .models import ArticleAmountRating

load_dotenv()


@shared_task
def my_task(compaign_id):
    from .views import access_token

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
