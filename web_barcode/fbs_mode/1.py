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
from helpers import (print_barcode_to_pdf2, qrcode_print_for_products,
                     special_design_dark, special_design_light,
                     supply_qrcode_to_standart_view)
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

headers_karavaev = {
    'Api-Key': os.getenv('API_KEY_OZON_KARAVAEV'),
    'Content-Type': 'application/json',
    'Client-Id': os.getenv('CLIENT_ID_OZON_KARAVAEV')
}


class OzonFbsMode():
    """Класс отвечает за работу с заказами ОЗОН"""

    def __init__(self):
        # Данные отправлений для FBS OZON
        self.posting_data = []

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
            "POST", url, headers=headers_karavaev, data=payload)

        for i in json.loads(response.text)['result']['postings']:

            inner_dict_data = {}
            inner_dict_data['posting_number'] = i['posting_number']
            inner_dict_data['order_id'] = i['order_id']
            inner_dict_data['delivery_method'] = i['delivery_method']
            inner_dict_data['in_process_at'] = i['in_process_at']
            inner_dict_data['shipment_date'] = i['shipment_date']
            inner_dict_data['products'] = i['products']

            self.posting_data.append(inner_dict_data)
        for j in self.posting_data:
            print(j)
            print('***************')

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
                    "POST", url, headers=headers_karavaev, data=payload)
                print(json.loads(response.text))

    def prepare_data_for_confirm_delivery(self):
        """Подготовка данных для подтверждения отгрузки"""
        now_time = datetime.now()
        hour = now_time.hour
        day = datetime.today()
        amount_products = 0
        date_confirm_delivery = now_time + timedelta(days=1)
        date_confirm_delivery = date_confirm_delivery.strftime('%Y-%m-%d')

        for data_dict in self.posting_data:
            for sku_data in data_dict['products']:
                amount_products += sku_data['quantity']
        self.containers_count = math.ceil(amount_products/20)

        if hour >= 18 or hour <= 6:
            self.delivary_method_id = 22655170176000
            self.departure_date = date_confirm_delivery + 'T22:00:00Z'

        else:
            self.delivary_method_id = 1020000089903000
            self.departure_date = date_confirm_delivery + 'T08:00:00Z'

        # self.departure_date = self.posting_data[0]['shipment_date']

        print(self.containers_count)
        print(self.delivary_method_id)
        print(self.departure_date)

    def confirm_delivery_create_document(self):
        """Функция подтверждает отгрузку и запускает создание документов на стороне ОЗОН"""
        url = 'https://api-seller.ozon.ru/v2/posting/fbs/act/create'
        payload = json.dumps({
            "containers_count": self.containers_count,
            "delivery_method_id": self.delivary_method_id,
            "departure_date": self.departure_date
        })
        response = requests.request(
            "POST", url, headers=headers_karavaev, data=payload)
        print(json.loads(response.text))


# 1
ozon = OzonFbsMode()
ozon.awaiting_packaging_orders()
# 2
# ozon.awaiting_deliver_orders()
# 3
ozon.prepare_data_for_confirm_delivery()
# 4
# ozon.confirm_delivery_create_document()
