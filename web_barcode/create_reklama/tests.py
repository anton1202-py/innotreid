import json
import math
import os
import time
from datetime import datetime, timedelta

import requests
import telegram
from analytika_reklama.models import DailyCampaignParameters
from api_request.wb_requests import (advertisment_campaign_list,
                                     get_budget_adv_campaign)
from create_reklama.models import (CreatedCampaign, ProcentForAd,
                                   ReplenishWbCampaign,
                                   SenderStatisticDaysAmount)
from django.db.models import Sum
# from celery_tasks.celery import app
from dotenv import load_dotenv
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg
from reklama.models import DataOooWbArticle, OooWbArticle, UrLico

from web_barcode.constants_file import (CHAT_ID_ADMIN, CHAT_ID_EU,
                                        TELEGRAM_TOKEN, bot, header_ozon_dict,
                                        header_wb_dict, header_yandex_dict,
                                        ozon_adv_client_access_id_dict,
                                        ozon_adv_client_secret_dict,
                                        ozon_api_token_dict,
                                        wb_headers_karavaev, wb_headers_ooo,
                                        yandex_business_id_dict)

campaign_budget_users_list = [CHAT_ID_ADMIN, CHAT_ID_EU]


def camp_data():

    camp_all = CreatedCampaign.objects.all()

    for campaign in camp_all:
        header = header_wb_dict[campaign.ur_lico.ur_lice_name]
        campaign_numb = campaign.campaign_number
        data = view_statistic_adv_campaign(header, campaign_numb)
        mes = another_foo(campaign_numb, header, campaign)
        print(mes)


def view_statistic_adv_campaign(header, campaign):
    """Возвращает статистику показов рекламной кампании за вчерашний день"""
    days_delta = SenderStatisticDaysAmount.objects.get(id=1).days_amount + 1
    statistic_date_finish = datetime.now()
    statistic_date_start = statistic_date_finish - timedelta(days=days_delta)
    ur_lico = ''
    for ur_lico_data, header_data in header_wb_dict.items():
        if header_data == header:
            ur_lico = ur_lico_data

    if DailyCampaignParameters.objects.filter(
            campaign__ur_lico__ur_lice_name=ur_lico,
            campaign__campaign_number=str(campaign),
            statistic_date__gt=statistic_date_start,
            statistic_date__lt=statistic_date_finish
    ).exists():
        statistic_data = DailyCampaignParameters.objects.filter(
            campaign__ur_lico__ur_lice_name=ur_lico,
            campaign__campaign_number=campaign,
            statistic_date__gt=statistic_date_start,
            statistic_date__lt=statistic_date_finish
        ).aggregate(
            total_views=Sum('views'),
            total_clicks=Sum('clicks'),
            total_orders=Sum('orders')
        )

        # Обрабатываем случай, если total_views = None
        total_views = statistic_data['total_views'] or 0
        # Обрабатываем случай, если total_clicks = None
        total_clicks = statistic_data['total_clicks'] or 0

        # Вычисляем total_ctr
        total_ctr = round((total_clicks / total_views *
                           100), 2) if total_views > 0 else 0

        # Добавляем total_ctr в результат
        statistic_data['total_ctr'] = total_ctr

        return statistic_data
    else:
        return None


def another_foo(campaign, header, campaign_obj):
    view_statistic = view_statistic_adv_campaign(header, campaign)
    # Показы
    view_count = ''
    # Переходы
    view_clicks = ''
    # CTR
    view_ctr = ''
    # Заказы
    view_orders = ''
    statistic_date = ''
    if view_statistic:
        # Показы
        view_count = view_statistic['total_views']
        # Переходы
        view_clicks = view_statistic['total_clicks']
        # CTR
        view_ctr = view_statistic['total_ctr']
        # Заказы
        view_orders = view_statistic['total_orders']
        statistic_date = SenderStatisticDaysAmount.objects.get(
            id=1).days_amount
    if view_statistic:
        message = (f"Пополнил {campaign}: {campaign_obj.campaign_name}. \nПоказов: {view_count}.\nПереходов: {view_clicks}.\nCTR: {view_ctr}.\nЗаказов: {view_orders}."
                   f"Статистика за последние : {statistic_date} дней")
    else:
        message = (f"Пополнил {campaign}.**********************************")
    return message
