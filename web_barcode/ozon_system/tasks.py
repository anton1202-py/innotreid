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

from web_barcode.constants_file import (CHAT_ID_ADMIN, TELEGRAM_TOKEN, bot,
                                        header_ozon_dict, header_wb_dict,
                                        header_yandex_dict,
                                        wb_headers_karavaev, wb_headers_ooo,
                                        yandex_business_id_dict)

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
    если цена в акции меньше, чем в базе даных
    """
    for ur_lico, header in header_ozon_dict.items():
        delete_articles_with_low_price(header, ur_lico)
    text = 'Отработала функция ozon_system.tasks.delete_ozon_articles_with_low_price_from_actions'
    bot.send_message(chat_id=CHAT_ID_ADMIN,
                     text=text, parse_mode='HTML')
