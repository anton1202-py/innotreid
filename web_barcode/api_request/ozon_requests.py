import json
import math
import os
import time
from datetime import datetime, timedelta

import requests
import telegram
from django.contrib.auth.models import User
# from celery_tasks.celery import app
from dotenv import load_dotenv
from price_system.models import Articles, DesignUser
from price_system.supplyment import sender_error_to_tg
from reklama.models import (AdvertisingCampaign, CompanyStatistic,
                            DataOooWbArticle, OooWbArticle, OzonCampaign,
                            ProcentForAd, SalesArticleStatistic,
                            WbArticleCommon, WbArticleCompany)

from web_barcode.constants_file import (CHAT_ID_ADMIN, TELEGRAM_TOKEN, bot,
                                        header_ozon_dict, header_wb_data_dict,
                                        header_wb_dict, header_yandex_dict,
                                        ozon_adv_client_access_id_dict,
                                        ozon_adv_client_secret_dict,
                                        ozon_api_token_dict,
                                        wb_headers_karavaev, wb_headers_ooo,
                                        yandex_business_id_dict)


def ozon_sales_monthly_report(header, month, year, attempt=0):
    """Получаем данные всех артикулов в ВБ. Максимум 1 запрос в минут"""
    url = f'https://api-seller.ozon.ru/v2/finance/realization'
    payload = json.dumps({
        "month": month,
        "year": year
    })
    response = requests.request(
        "POST", url, headers=header, data=payload)
    attempt += 1
    message = ''
    if attempt <= 50:
        if response.status_code == 200:
            all_data = json.loads(response.text)
            return all_data
        else:
            time.sleep(65)

            return ozon_sales_monthly_report(header, month, year, attempt)
    elif response.status_code == 403:
        message = f'статус код {response.status_code}. Доступ запрещен'
    elif response.status_code == 429:
        message = f'статус код {response.status_code}. Слишком много запросов'
    elif response.status_code == 401:
        message = f'статус код {response.status_code}. Не авторизован'
    else:
        message = f'статус код {response.status_code} у получения инфы всех артикулов ООО ВБ'

    if message:
        message = f'api_request. wb_sales_statistic. {message}'
        bot.send_message(chat_id=CHAT_ID_ADMIN, text=message)
