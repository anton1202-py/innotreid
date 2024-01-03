import base64
import glob
import io
import json
import math
import os
import shutil
import time
from collections import Counter
from contextlib import closing
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

import dropbox
import img2pdf
import openpyxl
import pandas as pd
import psycopg2
import pythoncom
import requests
import win32com.client as win32
from barcode import Code128
from barcode.writer import ImageWriter
from dotenv import load_dotenv
from helpers import (merge_barcode_for_ozon_two_on_two,
                     new_data_for_ozon_ticket, print_barcode_to_pdf2,
                     qrcode_print_for_products, special_design_dark,
                     special_design_light, supply_qrcode_to_standart_view)
from openpyxl import Workbook, load_workbook
from openpyxl.drawing import image
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from PIL import Image, ImageDraw, ImageFont
from PyPDF3 import PdfFileReader, PdfFileWriter
from PyPDF3.pdf import PageObject
from sqlalchemy import create_engine
from win32com.client import DispatchEx

dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')

load_dotenv(dotenv_path)

ozon_headers_karavaev = {
    'Api-Key': os.getenv('API_KEY_OZON_KARAVAEV'),
    'Content-Type': 'application/json',
    'Client-Id': os.getenv('CLIENT_ID_OZON_KARAVAEV')
}

REFRESH_TOKEN_DB = os.getenv('REFRESH_TOKEN_DB')
APP_KEY_DB = os.getenv('APP_KEY_DB')
APP_SECRET_DB = os.getenv('APP_SECRET_DB')
API_KEY_WB_IP = os.getenv('API_KEY_WB_IP')

dbx_db = dropbox.Dropbox(oauth2_refresh_token=REFRESH_TOKEN_DB,
                         app_key=APP_KEY_DB,
                         app_secret=APP_SECRET_DB)


class OzonFbsMode():
    """Класс отвечает за работу с заказами ОЗОН"""

    def __init__(self):
        # Данные отправлений для FBS OZON
        self.posting_data = []
        self.warehouse_list = [1020000089903000, 22655170176000]
        self.date_for_files = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
        self.main_save_folder_selver = 'web_barcode/fbs_mode/data_for_barcodes'
        self.dropbox_main_fbs_folder = '/DATABASE/beta'

    def awaiting_packaging_orders(self):
        """
        Функция собирает новые заказы и преобразует данные
        от заказа в словарь для дальнейшей работы с ним
        """
        # Метод для просмотра новых заказов
        url = "https://api-seller.ozon.ru/v3/posting/fbs/unfulfilled/list"

        payload = json.dumps({
            "dir": "ASC",
            "filter": {
                "cutoff_from": "2023-12-22T14:15:22Z",
                "cutoff_to": "2023-12-31T14:15:22Z",
                "delivery_method_id": [],
                "provider_id": [],
                "status": "awaiting_packaging",
                "warehouse_id": []
            },
            "limit": 100,
            "offset": 0,
            "with": {
                "analytics_data": True,
                "barcodes": True,
                "financial_data": True,
                "translit": True
            }
        })

        response = requests.request(
            "POST", url, headers=ozon_headers_karavaev, data=payload)
        for i in json.loads(response.text)['result']['postings']:

            inner_dict_data = {}
            inner_dict_data['posting_number'] = i['posting_number']
            inner_dict_data['order_id'] = i['order_id']
            inner_dict_data['delivery_method'] = i['delivery_method']
            inner_dict_data['in_process_at'] = i['in_process_at']
            inner_dict_data['shipment_date'] = i['shipment_date']
            inner_dict_data['products'] = i['products']

            self.posting_data.append(inner_dict_data)
        # for j in self.posting_data:
        #     print(j)
        #     print('***************')

    def awaiting_deliver_orders(self):
        """
        Делит заказ на отправления и переводит его в статус awaiting_deliver.
        Каждый элемент в packages может содержать несколько элементов products или отправлений.
        Каждый элемент в products — это товар, включённый в данное отправление.
        """
        url = 'https://api-seller.ozon.ru/v4/posting/fbs/ship'
        for data_dict in self.posting_data:
            # print('posting_number', posting_number)
            # print('data_list', data_list)
            for sku_data in data_dict['products']:
                # print('sku_data[sku]', sku_data['sku'])
                # print('sku_data[quantity]', sku_data['quantity'])
                payload = json.dumps({
                    "packages": [
                        {
                            "products": [
                                {
                                    "product_id": sku_data['sku'],
                                    "quantity": sku_data['quantity']
                                }
                            ]
                        }
                    ],
                    "posting_number": data_dict['posting_number'],
                    "with": {
                        "additional_data": True
                    }
                })
                response = requests.request(
                    "POST", url, headers=ozon_headers_karavaev, data=payload)

    def prepare_data_for_confirm_delivery(self):
        """Подготовка данных для подтверждения отгрузки"""
        now_time = datetime.now()
        hour = now_time.hour
        date_folder = datetime.today().strftime('%Y-%m-%d')

        date_before = now_time - timedelta(days=20)
        tomorrow_date = now_time + timedelta(days=1)

        since_date_for_filter = date_before.strftime(
            '%Y-%m-%d') + 'T08:00:00Z'
        to_date_for_filter = tomorrow_date.strftime(
            '%Y-%m-%d') + 'T23:59:00Z'
        date_confirm_delivery = now_time + timedelta(days=1)
        date_confirm_delivery = date_confirm_delivery.strftime('%Y-%m-%d')

        # Проверяем все отгрузки, которые буду завтра
        url = 'https://api-seller.ozon.ru/v3/posting/fbs/list'

        # Словарь с данными {'Номер склада': {quantity: 'Количество артикулов', containers_count: 'количество коробок'}}
        self.ware_house_amount_dict = {}
        # Словарь с данными {'номер отправления': {'артикул продавца': 'количество'}}
        self.fbs_ozon_common_data = {}
        # Словарь с данными {'артикул продавца': 'количество'}. Для сводной таблицы по FBS
        self.ozon_article_amount = {}

        if hour >= 18 or hour <= 6:
            self.delivary_method_id = 22655170176000
            self.dropbox_current_assembling_folder = f'{self.dropbox_main_fbs_folder}/НОЧЬ СБОРКА ФБС/{date_folder}'
        else:
            self.delivary_method_id = 1020000089903000
            self.dropbox_current_assembling_folder = f'{self.dropbox_main_fbs_folder}/НОЧЬ СБОРКА ФБС/{date_folder}'
        self.departure_date = date_confirm_delivery + 'T10:00:00Z'

        amount_products = 0
        payload = json.dumps(
            {
                "dir": "asc",
                "filter": {
                    "delivery_method_id": [self.delivary_method_id],
                    "provider_id": [24],
                    "since": since_date_for_filter,
                    "status": "awaiting_deliver",
                    "to": to_date_for_filter,
                    "warehouse_id": [self.delivary_method_id]
                },
                "limit": 999,
                "offset": 0,
                "with": {
                    "analytics_data": True,
                    "barcodes": True,
                    "financial_data": True,
                    "translit": True
                }
            }
        )
        response = requests.request(
            "POST", url, headers=ozon_headers_karavaev, data=payload)
        for data in json.loads(response.text)['result']['postings']:
            inner_article_amount_dict = {}

            # if tomorrow_date.strftime('%Y-%m-%d') in data["shipment_date"]:
            if '29' in data["shipment_date"]:
                for product in data['products']:
                    amount_products += product['quantity']
                    inner_article_amount_dict[product['offer_id']
                                              ] = product['quantity']
                    if product['offer_id'] not in self.ozon_article_amount.keys():
                        self.ozon_article_amount[product['offer_id']] = int(
                            product['quantity'])
                    else:
                        self.ozon_article_amount[product['offer_id']
                                                 ] = self.ozon_article_amount[product['offer_id']] + int(product['quantity'])
                self.fbs_ozon_common_data[data['posting_number']
                                          ] = inner_article_amount_dict
        containers_count = math.ceil(amount_products/20)
        self.ware_house_amount_dict[self.delivary_method_id] = {
            'quantity': amount_products, 'containers_count': containers_count}

        # print(self.delivary_method_id)
        # print(self.departure_date)
        print('self.ware_house_amount_dict', self.ware_house_amount_dict)
        print('self.fbs_ozon_common_data', self.fbs_ozon_common_data)
        print('self.ozon_article_amount', self.ozon_article_amount)

    def confirm_delivery_create_document(self):
        """Функция подтверждает отгрузку и запускает создание документов на стороне ОЗОН"""
        url = 'https://api-seller.ozon.ru/v2/posting/fbs/act/create'
        if self.ware_house_amount_dict[self.delivary_method_id]['quantity'] > 0:
            payload = json.dumps({
                "containers_count": self.ware_house_amount_dict[self.delivary_method_id]['containers_count'],
                "delivery_method_id": self.delivary_method_id,
                "departure_date": self.departure_date
            })
            response = requests.request(
                "POST", url, headers=ozon_headers_karavaev, data=payload)
            self.delivery_id = json.loads(response.text)['result']['id']

    def check_delivery_create(self):
        """
        Функция проверяет, что отгрузка создана.
        Формирует список отправлений для дальнейшей работы
        """
        url = 'https://api-seller.ozon.ru/v2/posting/fbs/act/check-status'

        payload = json.dumps(
            {
                "id": self.delivery_id
                # "id": 35178630
            }
        )
        response = requests.request(
            "POST", url, headers=ozon_headers_karavaev, data=payload)

        data = json.loads(response.text)['result']
        if data['status'] == "ready":

            self.delivery_number_list = data["added_to_act"]
            print('Функция check_delivery_create сработала. Спать 5 мин не нужно')
        else:
            print('уснули на 5 мин в функции check_delivery_create')
            time.sleep(300)
            self.check_delivery_create()

    def receive_barcode_delivery(self):
        """Получает и сохраняет штрихкод поставки"""
        url = 'https://api-seller.ozon.ru/v2/posting/fbs/act/get-barcode'
        payload = json.dumps(
            {
                # "id": self.delivery_id
                "id": 35275670
            }
        )
        self.delivery_id = 35275670
        response = requests.request(
            "POST", url, headers=ozon_headers_karavaev, data=payload)

        image = Image.open(io.BytesIO(response.content))
        save_folder_docs = f"{self.main_save_folder_selver}/ozon_delivery_barcode/{self.delivery_id}_баркод {self.date_for_files}.png"
        image.save(save_folder_docs)
        folder = (
            f'{self.dropbox_current_assembling_folder}/OZON-ИП акт поставки {self.date_for_files}.png')
        with open(save_folder_docs, 'rb') as f:
            dbx_db.files_upload(f.read(), folder)

    def check_status_formed_invoice(self):
        """
        Проверяет статус формирования накладной: /v2/posting/fbs/digital/act/check-status. 
        Когда статус документа перейдёт в FORMED или CONFIRMED, получите файлы:
        Транспортная накладная: /v2/posting/fbs/act/get-pdf.
        Лист отгрузки: /v2/posting/fbs/digital/act/get-pdf.
        """

        url = 'https://api-seller.ozon.ru/v2/posting/fbs/digital/act/check-status'
        payload = json.dumps(
            {
                "id": self.delivery_id
                # "id": 35178630
            }
        )
        response = requests.request(
            "POST", url, headers=ozon_headers_karavaev, data=payload)

        data = json.loads(response.text)['status']

        if data == "CONFIRMED" or data == "FORMED":
            print('Функция check_status_formed_invoice сработала. Спать 5 мин не нужно')
            self.receive_barcode_delivery()
            self.get_box_tickets()
            self.forming_package_ticket_with_article()
        else:
            print('уснули на 5 мин в функции check_status_formed_invoice')
            time.sleep(300)
            self.check_status_formed_invoice()

    def get_box_tickets(self):
        """
        Функция получает и сохраняет этикетки для каждой коробки в формате PDF.
        Данные получают из эндпоинта /v2/posting/fbs/act/get-container-labels.
        """
        url = 'https://api-seller.ozon.ru/v2/posting/fbs/act/get-container-labels'

        payload = json.dumps(
            {
                # "id": self.delivery_id
                "id": 35275670
            }
        )
        response = requests.request(
            "POST", url, headers=ozon_headers_karavaev, data=payload)

        # получение данных PDF из входящих данных
        pdf_data = response.content  # замените на фактические входные данные
        save_folder_docs = f'{self.main_save_folder_selver}/ozon_docs/OZON - ИП ШК на 1 коробку {self.date_for_files}.pdf'
        # сохранение PDF-файла
        with open(save_folder_docs, 'wb') as f:
            f.write(pdf_data)
        folder = (
            f'{self.dropbox_current_assembling_folder}/OZON-ИП ШК на 1 коробку {self.date_for_files}.pdf')
        with open(save_folder_docs, 'rb') as f:
            dbx_db.files_upload(f.read(), folder)

    def forming_package_ticket_with_article(self):
        """
        Функция получает и сохраняет этикетки этикетки для каждой отправки.
        Данные получают из эндпоинта /v2/posting/fbs/package-label.
        После получения и сохранения всех этикеток помещает артикул продавца
        на этикетку.
        """
        url = 'https://api-seller.ozon.ru/v2/posting/fbs/package-label'
        for package in self.fbs_ozon_common_data.keys():
            payload = json.dumps(
                {
                    "posting_number": [package]
                }
            )
            response = requests.request(
                "POST", url, headers=ozon_headers_karavaev, data=payload)
            save_folder = f'{self.main_save_folder_selver}/package_tickets'
            save_folder_docs = f'{self.main_save_folder_selver}/package_tickets/{package}.pdf'
            # сохранение PDF-файла
            with open(save_folder_docs, 'wb') as f:
                f.write(response.content)

        # Записываем артикул продавциа в файл с этикеткой
        new_data_for_ozon_ticket(save_folder, self.fbs_ozon_common_data)
        # Формируем список всех файлов, которые нужно объединять в один документ
        done_files_folder = f'{self.main_save_folder_selver}/package_tickets/done'
        list_filename = glob.glob(f'{done_files_folder}/*.pdf')
        # Адрес и имя конечного файла
        file_name = f'{self.main_save_folder_selver}/package_tickets/done/done_tickets.pdf'
        merge_barcode_for_ozon_two_on_two(list_filename, file_name)
        folder = f'{self.dropbox_current_assembling_folder}/OZON-ИП этикетки.pdf'
        with open(file_name, 'rb') as f:
            dbx_db.files_upload(f.read(), folder)


# 1 собирает новые заказы и преобразует данные
# от заказа в словарь для дальнейшей работы с ним
ozon = OzonFbsMode()
# ozon.awaiting_packaging_orders()
# 2 Делит заказ на отправления и переводит его в статус awaiting_deliver
# ozon.awaiting_deliver_orders()
# 3 Подготовка данных для подтверждения отгрузки
ozon.prepare_data_for_confirm_delivery()
# 4 подтверждает отгрузку и запускает создание документов на стороне ОЗОН
# ozon.confirm_delivery_create_document()

# 5 Проверяет, что поставка создалась
# ozon.check_delivery_create()

# 6 Создаю и сохраняю баркод поставки Озон
# ozon.receive_barcode_delivery()

# 7 Сохраняем траспортную накладную
# ozon.check_status_formed_invoice()
ozon.receive_barcode_delivery()
ozon.get_box_tickets()
