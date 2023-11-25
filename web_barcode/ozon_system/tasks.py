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
from ozon_system.models import (AdvGroup, ArticleAmountRating, DateActionInfo,
                                GroupActions, GroupCeleryAction, GroupCompaign)

from .celery import app

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


@shared_task
def start_group(group_number):
    from ozon_system.views import access_token
    logger.info("Функция my_task приняла задание для group_number %s в %s",
                group_number, datetime.now())
    compaign_list = AdvCompaignGroup.objects.filter(
        group_number=group_number).values_list('campaigns', flat=True)

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token()}',
    }
    for compaign_id in compaign_list:
        url = f"https://performance.ozon.ru:443/api/client/campaign/{compaign_id}/activate"
        payload_active = json.dumps({
            "campaignId": compaign_id
        })
        response = requests.request(
            "POST", url, headers=headers, data=payload_active)


@shared_task
def stop_group(group_number):
    from ozon_system.views import access_token
    logger.info("Функция my_task приняла задание для group_number %s в %s",
                group_number, datetime.now())
    compaign_list = AdvCompaignGroup.objects.filter(
        group_number=group_number).values_list('campaigns', flat=True)

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token()}',
    }
    for compaign_id in compaign_list:
        url = f"https://performance.ozon.ru:443/api/client/campaign/{compaign_id}/deactivate"
        payload_deactive = json.dumps({
            "campaignId": compaign_id
        })
        response = requests.request(
            "POST", url, headers=headers, data=payload_deactive)
