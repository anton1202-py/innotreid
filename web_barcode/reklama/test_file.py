import json
import math
import os
import time
from datetime import datetime, timedelta

import requests
import telegram
# from celery_tasks.celery import app
from dotenv import load_dotenv
from price_system.models import Articles
from reklama.models import DataOooWbArticle

# from price_system.supplyment import sender_error_to_tg
# from reklama.models import (AdvertisingCampaign, CompanyStatistic,
#                            DataOooWbArticle, OooWbArticle, OzonCampaign,
#                           ProcentForAd, SalesArticleStatistic,
#                            WbArticleCommon, WbArticleCompany)

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

ozon_adv_client_access_id_dict = {
    'ООО Иннотрейд': OZON_OOO_ADV_CLIENT_ACCESS_ID,
    'ИП Караваев': OZON_IP_ADV_CLIENT_ACCESS_ID
}

ozon_adv_client_secret_dict = {
    'ООО Иннотрейд': OZON_OOO_ADV_CLIENT_SECRET,
    'ИП Караваев': OZON_IP_ADV_CLIENT_SECRET
}

ozon_api_token_dict = {
    'ООО Иннотрейд': OZON_OOO_API_TOKEN,
    'ИП Караваев': OZON_IP_API_TOKEN
}


def access_token(ur_lico):
    """
    Получение Bearer токена для работы с рекламным кабинетом.
    Выдается при каждом запросе в рекламный кабинет юр. лица.
    """
    url = "https://performance.ozon.ru/api/client/token"

    payload = json.dumps({
        "client_id": ozon_adv_client_access_id_dict[ur_lico],
        "client_secret": ozon_adv_client_secret_dict[ur_lico],
        "grant_type": "client_credentials"
    })
    headers = {
        'Content-Type': 'application/json',
        'Headers': ozon_api_token_dict[ur_lico],
    }

    response = requests.request(
        "POST", url, headers=ozon_header[ur_lico], data=payload)
    print(json.loads(response.text)['access_token'])
    return json.loads(response.text)['access_token']


def ozon_get_adv_campaign_list(ur_lico):
    """
    ПОлучает список рекламных кампаний входящего юр лица
    """
    url = 'https://performance.ozon.ru:443/api/client/campaign'
    header = ozon_header[ur_lico]
    header['Authorization'] = f'Bearer {access_token(ur_lico)}'
    response = requests.request("GET", url, headers=header)
    ozon_adv_list = json.loads(response.text)['list']
    return ozon_adv_list


def ozon_get_campaign_data(ur_lico):
    """Получает данные рекламных кампаний ОЗОН. ID и название"""
    ozon_adv_list = ozon_get_adv_campaign_list(ur_lico)

    ozon_adv_info_dict = {}
    if ozon_adv_list:
        for i in ozon_adv_list:
            ozon_adv_info_dict[i['id']] = {'Название': i['title']}

    return ozon_adv_info_dict


def ozon_get_articles_data_adv_campaign(ur_lico, campaign, header):
    """Получает данные рекламной кампании"""
    url = f'https://performance.ozon.ru:443/api/client/campaign/{campaign}/objects'

    response = requests.request("GET", url, headers=header)
    articles_list = []
    if response.status_code == 200:
        articles_list = json.loads(response.text)['list']
    elif response.status_code == 404:
        print(f'Проверьте статус рекламной кампании {campaign}')
    return articles_list


def ozon_get_articles_in_adv_campaign(ur_lico, campaign, header):
    """Получает список артикулов рекламной кампании"""
    articles_data_list = ozon_get_articles_data_adv_campaign(
        ur_lico, campaign, header)
    articles_list = []

    for data in articles_data_list:
        articles_list.append(data['id'])
    return articles_list


def ozon_adv_campaign_articles_name_data(ur_lico):
    """
    Возвращает словарь с данными кампании по артикулам и названию
    Вид словаря: {кампания: {'Название': 'Название кампании', 'Артикулы': [Список артикулов]}}
    """
    campaigns_data = ozon_get_campaign_data(ur_lico)
    header = ozon_header[ur_lico]
    header['Authorization'] = f'Bearer {access_token(ur_lico)}'
    for campaign, data in campaigns_data.items():
        articles_list = ozon_get_articles_in_adv_campaign(
            ur_lico, campaign, header)
        data['Артикулы'] = articles_list

    return campaigns_data


def ozon_add_campaign_data_to_database():
    """Добавляет данные рекламных кампаний в базу данных"""
    main_campaigns_data = ozon_adv_campaign_articles_name_data('ООО Иннотрейд')
    DataOooWbArticle.objects.all().update(ozon_ad_campaign=None)
    DataOooWbArticle.objects.all().update(ozon_campaigns_name=None)
    for campaign, campaigns_data in main_campaigns_data.items():
        if campaigns_data['Артикулы']:

            for article in campaigns_data['Артикулы']:
                article_obj = ''
                if Articles.objects.filter(ozon_product_id=int(article)).exists():
                    article_obj = Articles.objects.get(
                        ozon_product_id=article)
                elif Articles.objects.filter(ozon_sku=int(article)).exists():
                    article_obj = Articles.objects.get(
                        ozon_sku=article)
                elif Articles.objects.filter(ozon_fbo_sku_id=int(article)).exists():
                    article_obj = Articles.objects.get(
                        ozon_fbo_sku_id=article)
                elif Articles.objects.filter(ozon_fbs_sku_id=int(article)).exists():
                    article_obj = Articles.objects.get(
                        ozon_fbs_sku_id=article)
                if article_obj:
                    matching_data = DataOooWbArticle.objects.get(
                        wb_article=article_obj)
                    if matching_data.ozon_ad_campaign:
                        if str(campaign) not in str(matching_data.ozon_ad_campaign):
                            matching_data.ozon_ad_campaign = str(
                                matching_data.ozon_ad_campaign) + ', ' + str(campaign)
                    else:
                        matching_data.ozon_ad_campaign = campaign
                    if matching_data.ozon_campaigns_name:
                        if str(campaigns_data['Название']) not in str(matching_data.ozon_campaigns_name):
                            matching_data.ozon_campaigns_name = str(
                                matching_data.ozon_campaigns_name) + ', ' + str(campaigns_data['Название'])
                    else:
                        matching_data.ozon_campaigns_name = campaigns_data['Название']
                    matching_data.save()


# ozon_adv_campaign_articles_name_data('ООО Иннотрейд')
