import datetime
import json
import logging
import os
from collections import Counter
from datetime import datetime

import pandas as pd
import requests
import telegram
from celery import Celery, shared_task
from celery_tasks.celery import app
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from dotenv import load_dotenv
from ozon_system.models import (AdvGroup, ArticleAmountRating, DateActionInfo,
                                GroupActions, GroupCeleryAction, GroupCompaign)
from ozon_system.supplyment import delete_articles_with_low_price

# Загрузка переменных окружения из файла .env
dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)


REFRESH_TOKEN_DB = os.getenv('REFRESH_TOKEN_DB')
APP_KEY_DB = os.getenv('APP_KEY_DB')
APP_SECRET_DB = os.getenv('APP_SECRET_DB')

API_KEY_WB_IP = os.getenv('API_KEY_WB_IP')
YANDEX_IP_KEY = os.getenv('YANDEX_IP_KEY')

OZON_IP_API_TOKEN = os.getenv('OZON_IP__API_TOKEN')
API_KEY_OZON_KARAVAEV = os.getenv('API_KEY_OZON_KARAVAEV')
CLIENT_ID_OZON_KARAVAEV = os.getenv('CLIENT_ID_OZON_KARAVAEV')

OZON_OOO_API_TOKEN = os.getenv('OZON_OOO_API_TOKEN')
OZON_OOO_CLIENT_ID = os.getenv('OZON_OOO_CLIENT_ID')

OZON_IP_ADV_CLIENT_ACCESS_ID = os.getenv('OZON_IP_ADV_CLIENT_ACCESS_ID')
OZON_IP_ADV_CLIENT_SECRET = os.getenv('OZON_IP_ADV_CLIENT_SECRET')

OZON_OOO_ADV_CLIENT_ACCESS_ID = os.getenv('OZON_OOO_ADV_CLIENT_ACCESS_ID')
OZON_OOO_ADV_CLIENT_SECRET = os.getenv('OZON_OOO_ADV_CLIENT_SECRET')

YANDEX_OOO_KEY = os.getenv('YANDEX_OOO_KEY')
WB_OOO_API_KEY = os.getenv('WB_OOO_API_KEY')


TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID_ADMIN = os.getenv('CHAT_ID_ADMIN')
CHAT_ID_MANAGER = os.getenv('CHAT_ID_MANAGER')
CHAT_ID_EU = os.getenv('CHAT_ID_EU')
CHAT_ID_AN = os.getenv('CHAT_ID_AN')

campaign_budget_users_list = [CHAT_ID_ADMIN, CHAT_ID_EU]

bot = telegram.Bot(token=TELEGRAM_TOKEN)

wb_headers_karavaev = {
    'Content-Type': 'application/json',
    'Authorization': API_KEY_WB_IP
}
wb_headers_ooo = {
    'Content-Type': 'application/json',
    'Authorization': WB_OOO_API_KEY
}

ozon_headers_karavaev = {
    'Api-Key': OZON_IP_API_TOKEN,
    'Content-Type': 'application/json',
    'Client-Id': CLIENT_ID_OZON_KARAVAEV
}
ozon_headers_ooo = {
    'Api-Key': OZON_OOO_API_TOKEN,
    'Content-Type': 'application/json',
    'Client-Id': OZON_OOO_CLIENT_ID
}

payload_ozon_adv_ooo = json.dumps({
    'client_id': OZON_OOO_ADV_CLIENT_ACCESS_ID,
    'client_secret': OZON_OOO_ADV_CLIENT_SECRET,
    "grant_type": "client_credentials"
})
payload_ozon_adv_ip = json.dumps({
    'client_id': OZON_IP_ADV_CLIENT_ACCESS_ID,
    'client_secret': OZON_IP_ADV_CLIENT_SECRET,
    'grant_type': 'client_credentials'
})

yandex_headers_karavaev = {
    'Authorization': YANDEX_IP_KEY,
}
yandex_headers_ooo = {
    'Authorization': YANDEX_OOO_KEY,
}

wb_header = {
    'ООО Иннотрейд': wb_headers_ooo,
    'ИП Караваев': wb_headers_karavaev
}

ozon_header = {
    'ООО Иннотрейд': ozon_headers_ooo,
    'ИП Караваев': ozon_headers_karavaev
}
ozon_payload = {
    'ООО Иннотрейд': payload_ozon_adv_ooo,
    'ИП Караваев': payload_ozon_adv_ip
}

logger = logging.getLogger(__name__)


@shared_task
def stop_compaign(compaign_id):
    """Останавливает рекламную кампанию ОЗОН"""
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
    """Запускает рекламную кампанию ОЗОН"""
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
    """Запускает группу рекламных кампаний ОЗОН"""
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
    """Останавливает группу рекламных кампаний ОЗОН"""
    compaigns_list = GroupCompaign.objects.all().values_list('compaign', flat=True)
    for compaign in compaigns_list:
        stop_compaign(compaign)


@app.task
def delete_ozon_articles_with_low_price_from_actions():
    """
    Удаляет артикулы из акций ОЗОН,
    если цна в акции меньше, чем в базе даных
    """
    ur_lico_list = ['ООО Иннотрейд', 'ИП Караваев']
    for url_lico in ur_lico_list:
        header = ozon_header[url_lico]
        delete_articles_with_low_price(header, url_lico)
