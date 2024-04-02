import json
import math
import os
import time
from datetime import datetime, timedelta

import requests
import telegram
# from celery_tasks.celery import app
from dotenv import load_dotenv
from price_system.models import ArticleGroup
from price_system.supplyment import sender_error_to_tg
from reklama.models import (AdvertisingCampaign, CompanyStatistic,
                            DataOooWbArticle, OooWbArticle, OzonCampaign,
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


def get_actions_list(header):
    """Получает список акций юр. лица."""
    url = 'https://api-seller.ozon.ru/v1/actions'
    headers = header
    response = requests.request("GET", url, headers=headers)
    actions_list = []
    if response.status_code == 200:
        main_data = json.loads(response.text)['result']
        for data in main_data:
            actions_list.append(data['id'])
        print('actions_list', actions_list)
        print('***********************')
        return actions_list
    else:
        message = 'ozon_system.supplyment.get_action_list Не получил данные от метода списка акций ОЗОН api-seller.ozon.ru/v1/actions'
        bot.send_message(chat_id=CHAT_ID_ADMIN, text=message)


def get_articles_data_from_database(ur_lico):
    """Получает данные артикулов из внутренней базы данных"""
    data = ArticleGroup.objects.filter(group__company=ur_lico)
    # Словарь вида {product_id: минимальная_цена}
    campaign_min_price_dict = {}
    for campaign_data in data:
        campaign_min_price_dict[campaign_data.common_article.ozon_product_id] = campaign_data.group.min_price
    return campaign_min_price_dict


def get_action_data(action_id, header, action_info_list=None, offset=0, koef=0):
    """
    Получает артикулы и их цену в акции
    Возвращает словарь вида: {артикул: цена_по_акции}
    """
    if action_info_list == None:
        action_info_list = []
    action_articles_info_dict = {}
    url = 'https://api-seller.ozon.ru/v1/actions/products'
    payload = json.dumps({
        "action_id": action_id,
        "limit": 100,
        "offset": offset
    })
    response = requests.request("POST", url, headers=header, data=payload)

    if response.status_code == 200:
        main_data = json.loads(response.text)['result']['products']
        print('len(main_data)', len(main_data))
        for data in main_data:
            action_info_list.append(data)
        if len(main_data) == 100:
            koef += 1
            print('koef', koef)
            offset = 100 * koef
            print('offset', offset)
            get_action_data(action_id, header, action_info_list, offset, koef)
        for action_data in action_info_list:
            action_articles_info_dict[action_data['id']
                                      ] = action_data['action_price']
        return action_articles_info_dict


def get_articles_price_from_actions(header):
    """
    Получает артикулы и их цену в акции.
    Возвращает словарь вида: {id_акции: {product_id: цена_по_акции}}
    """
    actions_list = get_actions_list(header)
    main_actions_info_dict = {}

    for action in actions_list:
        articles_action_price_dict = get_action_data(action, header)
        main_actions_info_dict[action] = articles_action_price_dict
        time.sleep(2)
    return main_actions_info_dict


def compare_action_articles_and_database(header, ur_lico):
    """Сравнивает артикулы из акций и из базы данных"""
    actions_data = get_articles_price_from_actions(header)

    database_data = get_articles_data_from_database(ur_lico)
    # Словарь для удаляемых артикулов ииз кампании
    del_articles = {}
    for action, action_articles in actions_data.items():
        inner_list = []
        for article, price in database_data.items():
            if article in action_articles:
                if action_articles[article] < database_data[article]:
                    inner_list.append(article)
                    print('ALARM', action, article,
                          action_articles[article], database_data[article])
        if inner_list:
            del_articles[action] = inner_list
    print('del_articles', del_articles)
    return del_articles


def del_articles_from_cation(header, action_id, articles_list):
    """Удаляет список артикулов из акции"""
    url = 'https://api-seller.ozon.ru/v1/actions/products/deactivate'
    payload = json.dumps({
        "action_id": action_id,
        "product_ids": articles_list
    })
    response = requests.request("POST", url, headers=header, data=payload)
    if response.status_code == 200:
        text = f'Из акции {action_id} удалили артикулы: {articles_list}'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=text, parse_mode='HTML')


def delete_articles_with_low_price(header, ur_lico):
    """
    Удаляет артикулы, цены которых а акциях ниже,
    чем выставленная минимальная цена
    """
    action_data = compare_action_articles_and_database(header, ur_lico)
    if action_data:
        for action_id, articles_list in action_data.items():
            del_articles_from_cation(header, action_id, articles_list)


def main_for_check():
    ur_lico_list = ['ООО Иннотрейд', 'ИП Караваев']
    for url_lico in ur_lico_list:
        header = ozon_header[url_lico]
        delete_articles_with_low_price(header, url_lico)
