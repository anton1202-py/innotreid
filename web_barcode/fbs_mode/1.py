import json
import os
import time

import requests
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)
API_KEY_WB_IP = os.getenv('API_KEY_WB_IP')
YANDEX_IP_KEY = os.getenv('YANDEX_IP_KEY')
API_KEY_OZON_KARAVAEV = os.getenv('API_KEY_OZON_KARAVAEV')
CLIENT_ID_OZON_KARAVAEV = os.getenv('CLIENT_ID_OZON_KARAVAEV')

OZON_OOO_API_TOKEN = os.getenv('OZON_OOO_API_TOKEN')
OZON_OOO_CLIENT_ID = os.getenv('OZON_OOO_CLIENT_ID')
YANDEX_OOO_KEY = os.getenv('YANDEX_OOO_KEY')
WB_OOO_API_KEY = os.getenv('WB_OOO_API_KEY')


TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID_ADMIN = os.getenv('CHAT_ID_ADMIN')
CHAT_ID_MANAGER = os.getenv('CHAT_ID_MANAGER')
CHAT_ID_EU = os.getenv('CHAT_ID_EU')
CHAT_ID_AN = os.getenv('CHAT_ID_AN')


wb_headers_karavaev = {
    'Content-Type': 'application/json',
    'Authorization': API_KEY_WB_IP
}
wb_headers_ooo = {
    'Content-Type': 'application/json',
    'Authorization': WB_OOO_API_KEY
}

ozon_headers_karavaev = {
    'Api-Key': API_KEY_OZON_KARAVAEV,
    'Content-Type': 'application/json',
    'Client-Id': CLIENT_ID_OZON_KARAVAEV
}
ozon_headers_ooo = {
    'Api-Key': OZON_OOO_API_TOKEN,
    'Content-Type': 'application/json',
    'Client-Id': OZON_OOO_CLIENT_ID
}


def delivery_data(next_number=0, limit_number=1000):
    url_data = f'https://suppliers-api.wildberries.ru/api/v3/supplies?limit={limit_number}&next={next_number}'
    response_data = requests.request(
        "GET", url_data, headers=wb_headers_karavaev)
    if response_data.status_code == 200:
        if len(json.loads(response_data.text)['supplies']) >= limit_number:
            next_number_new = json.loads(response_data.text)['next']
            return delivery_data(next_number_new)
        else:
            last_sup = json.loads(response_data.text)['supplies'][-1]
            supply_id = last_sup['id']
            return supply_id
    else:
        time.sleep(5)
        delivery_data()


def data_for_production_list():
    supply_id = delivery_data()
    url = f'https://suppliers-api.wildberries.ru/api/v3/supplies/{supply_id}/orders'
    response_data = requests.request(
        "GET", url, headers=wb_headers_karavaev)
    if response_data.status_code == 200:
        article_amount = {}
        orders_data = json.loads(response_data.text)['orders']
        for data in orders_data:
            if data['article'] in article_amount:
                article_amount[data['article']] += 1
            else:
                article_amount[data['article']] = 1
        return article_amount

    else:
        time.sleep(5)
        data_for_production_list()


print(data_for_production_list())
