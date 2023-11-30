import datetime
import json
import logging
import os
from collections import Counter
from datetime import datetime

import pandas as pd
import requests
from celery import Celery, shared_task
from celery_tasks.celery import app
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from dotenv import load_dotenv
from ozon_system.models import (AdvGroup, ArticleAmountRating, DateActionInfo,
                                GroupActions, GroupCeleryAction, GroupCompaign)

load_dotenv()

logger = logging.getLogger(__name__)


@shared_task
def stop_compaign(compaign_id):
    from ozon_system.views import access_token
    logger.info("Функция my_task приняла задание для compaign_id %s в %s",
                compaign_id, datetime.now())
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


@shared_task
def start_compaign(compaign_id):
    from ozon_system.views import access_token
    logger.info("Функция my_task приняла задание для compaign_id %s в %s",
                compaign_id, datetime.now())
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token()}',
    }
    url = f"https://performance.ozon.ru:443/api/client/campaign/{compaign_id}/activate"
    payload_deactive = json.dumps({
        "campaignId": compaign_id
    })
    response = requests.request(
        "POST", url, headers=headers, data=payload_deactive)


@app.task
def start_adv_company():
    today = datetime.now().date()
    group_list = AdvGroup.objects.all().values_list(
        'group', flat=True)
    data_group_dict = {}

    for group in group_list:
        data_group_dict[group] = GroupActions.objects.get(
            group=group, action_type='start').action_datetime

    for group, date_start in data_group_dict.items():
        months_passed = (today.year - date_start.year) * \
            12 + (today.month - date_start.month)
        if months_passed % 3 == 0:
            compaigns_list = GroupCompaign.objects.filter(
                group=group).values_list('compaign', flat=True)
            for compaign in compaigns_list:
                start_compaign(compaign)


@app.task
def stop_adv_company():
    compaigns_list = GroupCompaign.objects.all().values_list('compaign', flat=True)
    for compaign in compaigns_list:
        stop_compaign(compaign)
