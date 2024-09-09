import base64
import glob
import io
import json
import logging
import math
import os
import shutil
import smtplib
import textwrap
import time
import traceback
from collections import Counter
from contextlib import closing
from datetime import datetime, timedelta
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from pathlib import Path

import dropbox
import openpyxl
import pandas as pd
import psycopg2
import requests
import telegram
from celery_tasks.celery import app
from dotenv import load_dotenv
from msoffice2pdf import convert
from openpyxl import Workbook, load_workbook
from openpyxl.drawing import image
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from PIL import Image, ImageDraw, ImageFont
from price_system.supplyment import sender_error_to_tg
from sqlalchemy import create_engine

from web_barcode.constants_file import (CHAT_ID_ADMIN, CHAT_ID_AN, CHAT_ID_EU,
                                        CHAT_ID_MANAGER, EMAIL_ADDRESS_FROM,
                                        EMAIL_ADDRESS_FROM_PASSWORD,
                                        EMAIL_ADDRESS_TO,
                                        MANAGER_EMAIL_ADDRESS,
                                        NKS_EMAIL_ADDRESS, POST_PORT,
                                        POST_SERVER, bot, dbx_db,
                                        header_wb_dict, wb_headers_karavaev,
                                        wb_headers_ooo)

from .helpers import (design_barcodes_dict_spec,
                      merge_barcode_for_ozon_two_on_two,
                      merge_barcode_for_yandex_two_on_two,
                      new_data_for_ozon_ticket, new_data_for_yandex_ticket,
                      print_barcode_to_pdf2,
                      print_barcode_to_pdf_without_dropbox,
                      qrcode_print_for_products,
                      supply_qrcode_to_standart_view)

logging.basicConfig(level=logging.DEBUG,
                    filename="tasks_log.log",
                    format="%(asctime)s %(levelname)s %(message)s")

db_folder = '/!На производство'

file_add_name_ip = 'IP'
file_add_name_ooo = 'OOO'


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
            'fbs_mode/data_for_barcodes/new_pivot_excel',
            'fbs_mode/data_for_barcodes/photo',
            'fbs_mode/data_for_barcodes/raw_photo'
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


class WildberriesFbsMode():
    """Класс отвечает за работу с заказами Wildberries"""

    def __init__(self, headers, file_add_name):
        """Основные данные класса"""
        self.amount_articles = {}
        self.headers = headers
        self.file_add_name = file_add_name
        self.files_for_send = []

    def check_folder_exists(self, path):
        try:
            dbx_db.files_list_folder(path)
            return True
        except dropbox.exceptions.ApiError as e:
            return False

    @sender_error_to_tg
    def check_folder_availability(self, folder):
        """Проверяет наличие папки, если ее нет, то создает"""
        folder_path = os.path.join(
            os.getcwd(), folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    @sender_error_to_tg
    def convert_photo_from_webp_to_jpg(self, photo_address, article_barcode, name_raw_photo_folder, name_photo_folder):
        """Конвертирует webp изображение в jpg и сохраняет в нужных папках."""
        response = requests.get(photo_address)
        image = Image.open(BytesIO(response.content))
        name_raw_photo = f"{name_raw_photo_folder}/{article_barcode}.jpg"
        image.save(name_raw_photo)
        # Открываем изображение в формате We
        webp_image = Image.open(name_raw_photo)
        name_photo = f"{name_photo_folder}/{article_barcode}.jpg"
        # Сохраняем изображение в формате JPEG
        webp_image.save(name_photo, 'JPEG')
        return name_photo

    @sender_error_to_tg
    def process_new_orders(self):
        """
        WILDBERRIES
        Функция обрабатывает новые сборочные задания.
        """
        url = "https://suppliers-api.wildberries.ru/api/v3/orders/new"
        response = requests.request(
            "GET", url, headers=self.headers)
        if response.status_code == 200:
            returned_data_list = []
            orders_data = json.loads(response.text)['orders']
            # Сделал обход склада в НСК (его id = 1003917). Если склад = НСК, то товары не участвуют в сборке.
            for data in orders_data:
                if data['warehouseId'] == 1003917 or data['warehouseId'] == 1057680:
                    returned_data_list.append(data)
            return returned_data_list
        else:
            time.sleep(10)
            return self.process_new_orders()

    @sender_error_to_tg
    def time_filter_orders(self):
        """
        WILDBERRIES
        Функция фильтрует новые заказы по времени.
        Если заказ создан меньше, чем 1 час назад, в работу он не берется
        """
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

    @sender_error_to_tg
    def article_info(self, article):
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
            "POST", url_data, headers=self.headers, data=payload)
        if response_data.status_code == 200:
            return response_data.text
        else:
            text = f'Статус код = {response_data.status_code} у артикула {article}'
            bot.send_message(chat_id=CHAT_ID_ADMIN,
                             text=text, parse_mode='HTML')
            time.sleep(5)
            return self.article_info(article)

    @sender_error_to_tg
    def article_data_for_tickets(self):
        """
        WILDBERRIES
        Выделяет артикулы продавца светильников, их баркоды и наименования.
        Создает словарь с данными каждого артикулы и словарь с количеством каждого
        артикула. 
        """
        orders_data = [241422889]
        # Словарь с данными артикула: {артикул_продавца: [баркод, наименование]}
        self.data_article_info_dict = {}
        # Список только для артикулов ночников. Остальные отфильтровывает
        self.clear_article_list = []
        # Словарь для данных листа подбора {order_id: [photo_link, brand, name, seller_article]}
        self.selection_dict = {}
        # Папка для сохранения фото в webp формате
        name_raw_photo_folder = f"fbs_mode/data_for_barcodes/raw_photo"
        self.check_folder_availability(name_raw_photo_folder)
        # Папка для сохранения фото в jpg формате
        name_photo_folder = f"fbs_mode/data_for_barcodes/photo"
        self.check_folder_availability(name_photo_folder)
        CATEGORY_LIST = ['Ночники', 'Светильники']
        for data in orders_data:
            answer = self.article_info(data)
            if json.loads(answer)['cards']:
                if json.loads(answer)['cards'][0]['subjectName'] in CATEGORY_LIST:
                    self.clear_article_list.append(data)
                    # Достаем баркод артикула (первый из списка, если их несколько)
                    barcode = json.loads(answer)[
                        'cards'][0]['sizes'][0]['skus'][0]
                    # Достаем название артикула
                    title = json.loads(answer)[
                        'cards'][0]['title']
                    self.data_article_info_dict[data['article']] = [
                        title, barcode]
                    photo = json.loads(answer)[
                        'cards'][0]['photos'][1]['big']
                    photo_name = self.convert_photo_from_webp_to_jpg(
                        photo, barcode, name_raw_photo_folder, name_photo_folder)
                    title_article = json.loads(answer)[
                        'cards'][0]['title']
                    seller_article = data['article']
                    # Заполняем словарь данными для Листа подбора
                    self.selection_dict[data['id']] = [
                        title_article, seller_article]
            time.sleep(2)
        # Словарь с данными: {артикул_продавца: количество}
        self.amount_articles = dict(Counter(self.clear_article_list))
        return self.amount_articles

    
    def add_shelf_number_to_selection_dict(self, selection_dict: dict):
        """Добавляет полку хранения в словарь с данными отправления"""
        SHELVES_DATA = '/DATABASE/Стеллажи Новосибирск.xlsx'
        db_file_data = stream_dropbox_file(SHELVES_DATA)
        pd_file_data = pd.read_excel(db_file_data)
        special_tickets_data_file = pd.DataFrame(
            pd_file_data, columns=['Артикул', 'Ячейка'])
        articles_list = special_tickets_data_file['Артикул'].to_list()
        shelves_list = special_tickets_data_file['Ячейка'].to_list()
        article_address = {}
        for i in range(len(articles_list)):
            article = str(articles_list[i])
            address = str(shelves_list[i])
            if str(articles_list[i]) != 'nan':
                if article.capitalize() in article_address:
                    article_address[article.capitalize()] += f'\n{address}'
                else:
                    article_address[article.capitalize()] = address
        for _, order_data in selection_dict.items():
            if order_data[1].capitalize() in article_address:
                order_data.append(article_address[order_data[1].capitalize()])
            else:
                order_data.append('')
        return selection_dict

    

# ========== ВЫЗЫВАЕМ ФУНКЦИИ ПО ОЧЕРЕДИ ========== #


# ==================== Сборка WILDBERRIES =================== #

@sender_error_to_tg
def action_wb(file_add_name, headers_wb):
    wb_actions = WildberriesFbsMode(
        headers_wb, file_add_name)

    clearning_folders()
    # =========== АЛГОРИТМ  ДЕЙСТВИЙ С WILDBERRIES ========== #
    # 1. Создаю поставку
    wb_actions.create_delivery()
    # 2. добавляю сборочные задания по их id в созданную поставку и получаю qr стикер каждого
    # задания и сохраняю его в папку
    wb_actions.qrcode_order()
    # 3. Создаю лист сборки
    wb_actions.create_selection_list()
    # 4. Создаю шрихкоды для артикулов
    wb_actions.create_barcode_tickets()
    # 5. Добавляю поставку в доставку.
    wb_actions.supply_to_delivery()
    # 6. Получаю QR код поставки
    # и преобразует этот QR код в необходимый формат.
    wb_actions.qrcode_supply()
    # 7. Создаю список с полными именами файлов, которые нужно объединить
    wb_actions.list_for_print_create()
    # 8. Отрпавляю документы на элктронный адрес
    wb_actions.send_email()
    # 9. Отрпавляю данные о сборке в ТГ
    wb_actions.sender_message_to_telegram()


@app.task
def nsk_fbs_task():
    """Запускает утреннюю FBS сборку ИП (Без документов ОЗОН)"""
    try:
        action_wb(
            file_add_name_ip, wb_headers_karavaev)
        message_text = f'Сборка Новосибирск {file_add_name_ip} сформирована'
        bot.send_message(chat_id=CHAT_ID_MANAGER,
                         text=message_text, parse_mode='HTML')
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message_text, parse_mode='HTML')
    except:
        text = f'Приложение fbs_mode. Не сработала функция action_wb для ИП'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=text, parse_mode='HTML')

    try:
        time.sleep(60)
        action_wb(
            file_add_name_ooo, wb_headers_ooo)
        message_text = f'Сборка Новосибирск {file_add_name_ooo} сформирована'
        bot.send_message(chat_id=CHAT_ID_MANAGER,
                         text=message_text, parse_mode='HTML')
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message_text, parse_mode='HTML')
    except:
        text = f'Приложение fbs_mode. Не сработала функция action_wb для ООО'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=text, parse_mode='HTML')
