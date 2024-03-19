import json
import math
import os
import time
from datetime import datetime, timedelta

import requests
import telegram
# from celery_tasks.celery import app
from dotenv import load_dotenv
from price_system.supplyment import sender_error_to_tg
from reklama.models import (AdvertisingCampaign, CompanyStatistic,
                            OooWbArticle, OooWbArticleInfo, OzonCampaign,
                            ProcentForAd, SalesArticleStatistic,
                            WbArticleCommon, WbArticleCompany)

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

# =========== БЛОК РАБОТЫ С КАМПАНИЯМИ WILDBERRIES ========== #


def ooo_wb_articles_info(update_date=None, mn_id=0, common_data=None):
    """Получает информацию артикулов ООО ВБ от API WB"""
    if not common_data:
        common_data = []
    if update_date:
        cursor = {
            "limit": 1000,
            "updatedAt": update_date,
            "nmID": mn_id
        }
    else:
        cursor = {
            "limit": 1000,
            "nmID": mn_id
        }

    url = 'https://suppliers-api.wildberries.ru/content/v2/get/cards/list'
    payload = json.dumps(
        {
            "settings": {
                "cursor": cursor,
                "filter": {
                    "withPhoto": -1
                }
            }
        }
    )
    response = requests.request(
        "POST", url, headers=wb_header['ООО Иннотрейд'], data=payload)
    if response.status_code == 200:
        main_answer = json.loads(response.text)
        check_amount = main_answer['cursor']
        article_info = main_answer['cards']
        for data in article_info:
            inner_data = (data['vendorCode'], data['nmID'], data['title'])
            common_data.append(inner_data)
        print(check_amount)
        print(len(common_data))
        if len(article_info) == 1000:
            # time.sleep(5)
            ooo_wb_articles_info(
                check_amount['updatedAt'], check_amount['nmID'], common_data)
        return common_data
    else:
        message = f'статус код {response.status_code} у получения инфы всех артикулов ООО ВБ'


# print(ooo_wb_articles_info())


def ooo_wb_articles_data():
    """Записывает артикулы ООО ВБ в базу данных"""
    data = ooo_wb_articles_info()

    for entry in data:
        wb_article, wb_nomenclature, article_title = entry
        OooWbArticle.objects.get_or_create(
            wb_article=wb_article,
            wb_nomenclature=wb_nomenclature,
            article_title=article_title)

    # instances = [OooWbArticle(wb_article=entry[0], wb_nomenclature=entry[1],
    #                           article_title=entry[2])
    #              for entry in data]

    # # Используем bulk_create() для эффективной записи всех экземпляров в базу данных
    # OooWbArticle.objects.bulk_create(instances)
