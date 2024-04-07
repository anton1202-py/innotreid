import base64
import glob
import io
import json
import logging
import math
import os
import shutil
import textwrap
import time
import traceback
from collections import Counter
from datetime import datetime, timedelta

import dropbox
import requests
import telegram
from dotenv import load_dotenv
from openpyxl import Workbook, load_workbook
from openpyxl.drawing import image
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import create_engine

# Загрузка переменных окружения из файла .env
dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)

REFRESH_TOKEN_DB = os.getenv('REFRESH_TOKEN_DB')
APP_KEY_DB = os.getenv('APP_KEY_DB')
APP_SECRET_DB = os.getenv('APP_SECRET_DB')

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
    'Api-Key': API_KEY_OZON_KARAVAEV,
    'Content-Type': 'application/json',
    'Client-Id': CLIENT_ID_OZON_KARAVAEV
}
ozon_headers_ooo = {
    'Api-Key': OZON_OOO_API_TOKEN,
    'Content-Type': 'application/json',
    'Client-Id': OZON_OOO_CLIENT_ID
}

yandex_headers_karavaev = {
    'Authorization': YANDEX_IP_KEY,
}
yandex_headers_ooo = {
    'Authorization': YANDEX_OOO_KEY,
}

db_folder = '/!На производство'

file_add_name_ip = 'ИП'
file_add_name_ooo = 'ООО'

dbx_db = dropbox.Dropbox(oauth2_refresh_token=REFRESH_TOKEN_DB,
                         app_key=APP_KEY_DB,
                         app_secret=APP_SECRET_DB)

logging.basicConfig(level=logging.DEBUG,
                    filename="tasks_log.log",
                    format="%(asctime)s %(levelname)s %(message)s")


def process_new_orders():
    """
    WILDBERRIES
    Функция обрабатывает новые сборочные задания.
    """

    url = "https://suppliers-api.wildberries.ru/api/v3/orders/new"
    response = requests.request(
        "GET", url, headers=wb_headers_karavaev)
    orders_data = json.loads(response.text)['orders']
    if response.status_code == 200:
        return orders_data
    else:
        time.sleep(10)
        return process_new_orders()


def time_filter_orders():
    """
    WILDBERRIES
    Функция фильтрует новые заказы по времени.
    Если заказ создан меньше, чем 1 час назад, в работу он не берется
    """
    orders_data = process_new_orders()
    filters_order_data = []
    now_time = datetime.now()
    for order in orders_data:
        # Время создания заказа в переводе с UTC на московское
        create_order_time = datetime.strptime(
            order['createdAt'], '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=3)
        delta_order_time = now_time - create_order_time
        if delta_order_time > timedelta(hours=1):
            filters_order_data.append(order)
    return filters_order_data


def article_info(article):
    """
    WILDBERRIES
    Получает развернутый ответ про каждый артикул. 
    """
    url_data = "https://suppliers-api.wildberries.ru/content/v2/get/cards/list"
    payload = json.dumps({
        "settings": {
            "cursor": {
                "limit": 1
            },
            "filter": {
                "textSearch": article,
                "withPhoto": -1
            }
        }
    })
    response_data = requests.request(
        "POST", url_data, headers=wb_headers_karavaev, data=payload)
    if response_data.status_code == 200:
        print(article)
        print('*********************')
        print(response_data.text)
        print('*********************')
        print('*********************')
        return response_data.text
    else:
        text = f'Статус код = {response_data.status_code} у артикула {article}'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=text, parse_mode='HTML')
        time.sleep(5)
        return article_info(article)


def article_data_for_tickets():
    """
    WILDBERRIES
    Выделяет артикулы продавца светильников, их баркоды и наименования.
    Создает словарь с данными каждого артикулы и словарь с количеством каждого
    артикула. 
    """
    orders_data = time_filter_orders()
    # Словарь с данными артикула: {артикул_продавца: [баркод, наименование]}
    data_article_info_dict = {}
    # Список только для артикулов ночников. Остальные отфильтровывает
    clear_article_list = []
    # Словарь для данных листа подбора {order_id: [photo_link, brand, name, seller_article]}
    selection_dict = {}
    for data in orders_data:
        print(data['article'])
        print('***************')
        answer = article_info(data['article'])
        if json.loads(answer)['cards']:
            if json.loads(answer)['cards'][0]['subjectName'] == "Ночники":
                clear_article_list.append(data['article'])
                # Достаем баркод артикула (первый из списка, если их несколько)
                barcode = json.loads(answer)[
                    'cards'][0]['sizes'][0]['skus'][0]
                # Достаем название артикула
                title = json.loads(answer)[
                    'cards'][0]['title']
                data_article_info_dict[data['article']] = [
                    title, barcode]
                photo = json.loads(answer)[
                    'cards'][0]['photos'][0]['big']
                brand = json.loads(answer)[
                    'cards'][0]['brand']
                title_article = json.loads(answer)[
                    'cards'][0]['title']
                seller_article = data['article']
                # Заполняем словарь данными для Листа подбора
                selection_dict[data['id']] = [
                    photo, brand, title_article, seller_article]
        time.sleep(2)
    # Словарь с данными: {артикул_продавца: количество}
    amount_articles = dict(Counter(clear_article_list))
    return amount_articles


article_data_for_tickets()
