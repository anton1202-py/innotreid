import base64
import glob
import io
import json
import logging
import math
import os
import pprint
import shutil
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
import pythoncom
import requests
import telegram
from dotenv import load_dotenv
from openpyxl import Workbook, load_workbook
from openpyxl.drawing import image
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import create_engine
from win32com.client import DispatchEx

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

db_ip_folder = '/DATABASE/beta/ИП'
db_ooo_folder = '/DATABASE/beta/ООО'

file_add_name_ip = 'ИП'
file_add_name_ooo = 'ООО'

dbx_db = dropbox.Dropbox(oauth2_refresh_token=REFRESH_TOKEN_DB,
                         app_key=APP_KEY_DB,
                         app_secret=APP_SECRET_DB)

logging.basicConfig(level=logging.DEBUG, encoding='utf-8',
                    filename="fbs_mode/tasks_log.log", filemode="a",
                    format="%(asctime)s %(levelname)s %(message)s")


def stream_dropbox_file(path):
    _, res = dbx_db.files_download(path)
    with closing(res) as result:
        byte_data = result.content
        return io.BytesIO(byte_data)


def clearning_folders():
    dir = 'fbs_mode/data_for_barcodes/'
    for file_name in os.listdir(dir):
        file_path = os.path.join(dir, file_name)
        if os.path.isfile(file_path):
            os.unlink(file_path)

    dirs = ['fbs_mode/data_for_barcodes/cache_dir',
            'fbs_mode/data_for_barcodes/done_data',
            'fbs_mode/data_for_barcodes/pivot_excel',
            'fbs_mode/data_for_barcodes/qrcode_folder',
            'fbs_mode/data_for_barcodes/qrcode_supply',
            'fbs_mode/data_for_barcodes/package_tickets/done',
            'fbs_mode/data_for_barcodes/package_tickets',
            'fbs_mode/data_for_barcodes/ozon_docs',
            'fbs_mode/data_for_barcodes/ozon_delivery_barcode',
            'fbs_mode/data_for_barcodes/yandex'
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


class WildberriesFbsMode():
    """Класс отвечает за работу с заказами Wildberries"""

    def __init__(self, headers, db_forder, file_add_name):
        """Основные данные класса"""
        self.amount_articles = {}
        self.dropbox_main_fbs_folder = db_forder
        self.headers = headers
        self.file_add_name = file_add_name

    def check_folder_exists(self, path):
        try:
            dbx_db.files_list_folder(path)
            return True
        except dropbox.exceptions.ApiError as e:
            return False

    def create_dropbox_folder(self):
        """
        WILDBERRIES
        Создает папку для созданных документов на Дропбоксе.
        """
        hour = datetime.now().hour
        date_folder = datetime.today().strftime('%Y-%m-%d')

        if hour >= 6 and hour < 18:
            self.dropbox_current_assembling_folder = f'{self.dropbox_main_fbs_folder}/ДЕНЬ СБОРКА ФБС/{date_folder}'
        else:
            self.dropbox_current_assembling_folder = f'{self.dropbox_main_fbs_folder}/НОЧЬ СБОРКА ФБС/{date_folder}'
        # Создаем папку на dropbox, если ее еще нет
        if self.check_folder_exists(self.dropbox_current_assembling_folder) == False:
            dbx_db.files_create_folder_v2(
                self.dropbox_current_assembling_folder)

    def process_new_orders(self):
        """
        WILDBERRIES
        Функция обрабатывает новые сборочные задания.
        """
        try:
            url = "https://suppliers-api.wildberries.ru/api/v3/orders/new"
            response = requests.request(
                "GET", url, headers=self.headers)
            orders_data = json.loads(response.text)['orders']
            if response.status_code == 200:
                return orders_data
            else:
                time.sleep(10)
                return self.process_new_orders()
        except Exception as e:
            # обработка ошибки и отправка сообщения через бота
            message_text = error_message(
                'process_new_orders', self.process_new_orders, e)
            bot.send_message(chat_id=CHAT_ID_ADMIN,
                             text=message_text, parse_mode='HTML')

    def time_filter_orders(self):
        """
        WILDBERRIES
        Функция фильтрует новые заказы по времени.
        Если заказ создан меньше, чем 1 час назад, в работу он не берется
        """
        try:
            orders_data = self.process_new_orders()
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
        except Exception as e:
            # обработка ошибки и отправка сообщения через бота
            message_text = error_message(
                'time_filter_orders', self.time_filter_orders, e)
            bot.send_message(chat_id=CHAT_ID_ADMIN,
                             text=message_text, parse_mode='HTML')

    def article_info(self, article):
        """
        WILDBERRIES
        Получает развернутый ответ про каждый артикул. 
        """
        try:
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
                "POST", url_data, headers=self.headers, data=payload)
            if response_data.status_code == 200:
                return response_data.text
            else:
                text = f'Статус код = {response_data.status_code} у артикула {article}'
                bot.send_message(chat_id=CHAT_ID_ADMIN,
                                 text=text, parse_mode='HTML')
                time.sleep(5)
                return self.article_info(article)
        except Exception as e:
            # обработка ошибки и отправка сообщения через бота
            message_text = error_message(
                'article_info', self.article_info, e)
            bot.send_message(chat_id=CHAT_ID_ADMIN,
                             text=message_text, parse_mode='HTML')

    def article_data_for_tickets(self):
        """
        WILDBERRIES
        Выделяет артикулы продавца светильников, их баркоды и наименования.
        Создает словарь с данными каждого артикулы и словарь с количеством каждого
        артикула. 
        """

        orders_data = self.time_filter_orders()
        # Словарь с данными артикула: {артикул_продавца: [баркод, наименование]}
        self.data_article_info_dict = {}
        # Список только для артикулов ночников. Остальные отфильтровывает
        self.clear_article_list = []
        # Словарь для данных листа подбора {order_id: [photo_link, brand, name, seller_article]}
        self.selection_dict = {}
        for data in orders_data:
            answer = self.article_info(data['article'])
            print(answer)
            print('*****************')
            if json.loads(answer)['cards'][0]['subjectName'] == "Ночники":
                self.clear_article_list.append(data['article'])
                # Достаем баркод артикула (первый из списка, если их несколько)
                barcode = json.loads(answer)[
                    'cards'][0]['sizes'][0]['skus'][0]
                # Достаем название артикула
                title = json.loads(answer)[
                    'cards'][0]['title']
                self.data_article_info_dict[data['article']] = [
                    title, barcode]
                photo = json.loads(answer)[
                    'cards'][0]['photos'][0]['big']
                brand = json.loads(answer)[
                    'cards'][0]['brand']
                title_article = json.loads(answer)[
                    'cards'][0]['title']
                seller_article = data['article']
                # Заполняем словарь данными для Листа подбора
                self.selection_dict[data['id']] = [
                    photo, brand, title_article, seller_article]
            time.sleep(2)
        # Словарь с данными: {артикул_продавца: количество}
        self.amount_articles = dict(Counter(self.clear_article_list))
        return self.amount_articles


def action_wb(db_folder, file_add_name, headers_wb,
              headers_ozon, headers_yandex):
    wb_actions = WildberriesFbsMode(
        headers_wb, db_folder, file_add_name)

    clearning_folders()
    # =========== СОЗДАЮ СВОДНЫЙ ФАЙЛ ========== #
    # 1. Создаю сводный файл для производства

    wb_actions.article_data_for_tickets()

    # # # 4. добавляю сборочные задания по их id в созданную поставку и получаю qr стикер каждого
    # # # задания и сохраняю его в папку
    # # wb_actions.qrcode_order()
    # # 5. Создаю лист сборки
    # wb_actions.create_selection_list()
    # # # 6. Добавляю поставку в доставку, получаю QR код поставки
    # # # и преобразует этот QR код в необходимый формат.
    # # wb_actions.qrcode_supply()
    # # 7. Создаю список с полными именами файлов, которые нужно объединить
    # wb_actions.list_for_print_create()

    # clearning_folders()


action_wb(
    db_ooo_folder, file_add_name_ooo, wb_headers_ooo,
    ozon_headers_ooo, yandex_headers_ooo)
