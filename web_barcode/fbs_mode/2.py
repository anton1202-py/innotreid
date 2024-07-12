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
from contextlib import closing
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

import dropbox
import openpyxl
import pandas as pd
import psycopg2
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
headers = wb_headers_ooo
dbx_db = dropbox.Dropbox(oauth2_refresh_token=REFRESH_TOKEN_DB,
                         app_key=APP_KEY_DB,
                         app_secret=APP_SECRET_DB)

logging.basicConfig(level=logging.DEBUG,
                    filename="tasks_log.log",
                    format="%(asctime)s %(levelname)s %(message)s")


def stream_dropbox_file(path):
    _, res = dbx_db.files_download(path)
    with closing(res) as result:
        byte_data = result.content
        return io.BytesIO(byte_data)


def clearning_folders():
    dirs = ['fbs_mode/data_for_barcodes/cache_dir',
            'fbs_mode/data_for_barcodes/done_data',
            'fbs_mode/data_for_barcodes/pivot_excel',
            'fbs_mode/data_for_barcodes/qrcode_folder',
            'fbs_mode/data_for_barcodes/qrcode_supply',
            'fbs_mode/data_for_barcodes/package_tickets',
            'fbs_mode/data_for_barcodes/ozon_docs',
            'fbs_mode/data_for_barcodes/ozon_delivery_barcode',
            'fbs_mode/data_for_barcodes/yandex',
            'fbs_mode/data_for_barcodes/new_pivot_excel'
            ]
    for dir in dirs:
        for filename in glob.glob(os.path.join(dir, "*")):
            file_path = os.path.join(dir, filename)
            try:
                if os.path.isfile(filename) or os.path.islink(filename):
                    os.unlink(filename)
                elif os.path.isdir(filename):
                    shutil.rmtree(filename)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (filename, e))


def wb_clearning_folders():
    dirs = ['fbs_mode/data_for_barcodes/cache_dir',
            'fbs_mode/data_for_barcodes/done_data',
            'fbs_mode/data_for_barcodes/pivot_excel',
            'fbs_mode/data_for_barcodes/qrcode_folder',
            'fbs_mode/data_for_barcodes/qrcode_supply'
            ]
    for dir in dirs:
        for filename in glob.glob(os.path.join(dir, "*")):
            file_path = os.path.join(dir, filename)
            try:
                if os.path.isfile(filename) or os.path.islink(filename):
                    os.unlink(filename)
                elif os.path.isdir(filename):
                    shutil.rmtree(filename)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (filename, e))


def error_message(function_name: str, function, error_text: str) -> str:
    """
    Формирует текст ошибки и выводит информацию в модальном окне
    function_name - название функции.
    function - сама функция, как объект, а не результат работы. Без скобок.
    error_text - текст ошибки.
    """
    tb_str = traceback.format_exc()
    message_error = (f'Ошибка в функции: <b>{function_name}</b>\n'
                     f'<b>Функция выполняет</b>: {function.__doc__}\n'
                     f'<b>Ошибка</b>\n: {error_text}\n\n'
                     f'<b>Техническая информация</b>:\n {tb_str}')
    return message_error


def convert_photo_from_webp_to_jpg(photo_address, article_barcode, name_raw_photo_folder, name_photo_folder):
    """Конвертирует webp изображение в jpg и сохраняет в нужных папках."""
    response = requests.get(photo_address)
    image = Image.open(BytesIO(response.content))
    name_raw_photo = f"{name_raw_photo_folder}/{article_barcode}.jpg"
    print(photo_address, article_barcode)
    image.save(name_raw_photo)
    # Открываем изображение в формате We
    webp_image = Image.open(name_raw_photo)
    name_photo = f"{name_photo_folder}/{article_barcode}.jpg"
    # Сохраняем изображение в формате JPEG
    webp_image.save(name_photo, 'JPEG')
    return name_photo


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
        "POST", url_data, headers=headers, data=payload)
    if response_data.status_code == 200:
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
    orders_data = ['Мира_Единорог', 'Клим_Мишка', 'Лия_Мишка', 'Николь_Мишка', 'Эльвина_Мишка',
                   'krt03', 'S909', 'Ася_Мишка', 'Вика_Мишка', 'S964', 'S572', 'S904-13',
                   'N339-1', 'N355-1', 'N326-9', 'S977']
    # Словарь с данными артикула: {артикул_продавца: [баркод, наименование]}
    data_article_info_dict = {}
    # Список только для артикулов ночников. Остальные отфильтровывает
    clear_article_list = []
    # Словарь для данных листа подбора {order_id: [photo_link, brand, name, seller_article]}
    selection_dict = {}
    # Папка для сохранения фото в webp формате
    name_raw_photo_folder = f"fbs_mode/data_for_barcodes/raw_photo"

    # Папка для сохранения фото в jpg формате
    name_photo_folder = f"fbs_mode/data_for_barcodes/photo"

    CATEGORY_LIST = ['Ночники', 'Светильники']
    for data in orders_data:
        answer = article_info(data)
        if json.loads(answer)['cards']:
            if json.loads(answer)['cards'][0]['subjectName'] in CATEGORY_LIST:
                clear_article_list.append(data)
                # Достаем баркод артикула (первый из списка, если их несколько)
                barcode = json.loads(answer)[
                    'cards'][0]['sizes'][0]['skus'][0]
                # Достаем название артикула
                title = json.loads(answer)[
                    'cards'][0]['title']
                data_article_info_dict[data] = [
                    title, barcode]
                photo = json.loads(answer)[
                    'cards'][0]['photos'][1]['big']
                photo_name = convert_photo_from_webp_to_jpg(
                    photo, barcode, name_raw_photo_folder, name_photo_folder)
                brand = json.loads(answer)[
                    'cards'][0]['brand']
                title_article = json.loads(answer)[
                    'cards'][0]['title']
                seller_article = data
                # Заполняем словарь данными для Листа подбора
                # selection_dict[data['id']] = [
                #     photo_name, brand, title_article, seller_article]
        time.sleep(2)
    # Словарь с данными: {артикул_продавца: количество}
    amount_articles = dict(Counter(clear_article_list))
    print(amount_articles)
    return amount_articles


article_data_for_tickets()
