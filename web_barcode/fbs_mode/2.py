import base64
import glob
import io
import json
import math
import os
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
from helpers import (design_barcodes_dict_spec,
                     merge_barcode_for_ozon_two_on_two,
                     merge_barcode_for_yandex_two_on_two,
                     new_data_for_ozon_ticket, new_data_for_yandex_ticket,
                     print_barcode_to_pdf2, qrcode_print_for_products,
                     supply_qrcode_to_standart_view)
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

ozon_headers_karavaev = {
    'Api-Key': os.getenv('API_KEY_OZON_KARAVAEV'),
    'Content-Type': 'application/json',
    'Client-Id': os.getenv('CLIENT_ID_OZON_KARAVAEV')
}

yandex_headers_karavaev = {
    'Authorization': YANDEX_IP_KEY,
}

dbx_db = dropbox.Dropbox(oauth2_refresh_token=REFRESH_TOKEN_DB,
                         app_key=APP_KEY_DB,
                         app_secret=APP_SECRET_DB)


def clearning_folders():
    # dir = 'fbs_mode/data_for_barcodes/'
    # for file_name in os.listdir(dir):
    #    file_path = os.path.join(dir, file_name)
    #    if os.path.isfile(file_path):
    #        os.unlink(file_path)

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


class YandexMarketFbsMode():
    """Класс отвечает за работу с заказами Wildberries"""

    def __init__(self):
        """Основные данные класса"""
        self.amount_articles = {}
        self.dropbox_main_fbs_folder = '/DATABASE/beta'
        self.shipment_id = ''
        self.orders_list = []
        self.main_save_folder_server = 'fbs_mode/data_for_barcodes'
        self.date_for_files = datetime.now().strftime('%Y-%m-%d %H-%M')
        hour = datetime.now().hour
        date_folder = datetime.today().strftime('%Y-%m-%d')
        if hour >= 18 or hour <= 6:
            self.dropbox_current_assembling_folder = f'{self.dropbox_main_fbs_folder}/НОЧЬ СБОРКА ФБС/{date_folder}'
        else:
            self.dropbox_current_assembling_folder = f'{self.dropbox_main_fbs_folder}/ДЕНЬ СБОРКА ФБС/{date_folder}'

    def check_folder_exists(self, path):
        try:
            dbx_db.files_list_folder(path)
            return True
        except dropbox.exceptions.ApiError as e:
            return False

    def receive_orders_data(self):
        """
        YANDEXMARKET
        Функция обрабатывает заказы.
        Выделяет номера заказов, артикулы продавца в них, кол-во и название артикула.
        Создает список с данными каждого заказа: [{Заказ: [{артикул_продавца: артикул, название_артикула: название,
        количество_в_заказе: количество}]}]
        """
        url = "https://api.partner.market.yandex.ru/campaigns/23746359/orders?status=PROCESSING&substatus=STARTED"
        response = requests.request(
            "GET", url, headers=yandex_headers_karavaev)

        orders_list = json.loads(response.text)['orders']

        main_orders_list = []
        for order in orders_list:
            order_dict = {}
            article_list_in_order = order['items']
            inner_article_list = []
            inner_article_dict = {}
            for article in article_list_in_order:

                inner_article_dict = {}

                inner_article_dict['seller_article'] = article['offerId']
                inner_article_dict['article_name'] = article['offerName']
                inner_article_dict['amount'] = article['count']

                inner_article_list.append(inner_article_dict)
            inner_article_dict['articles_info'] = inner_article_list
            inner_article_dict['delivery_date'] = order['delivery']['dates']['toDate']
            order_dict['order_id'] = order['id']
            order_dict['order_data'] = inner_article_dict

            main_orders_list.append(order_dict)
        return main_orders_list

    def change_orders_status(self):
        """
        YANDEXMARKET
        Функция изменяет статус новых заказов.
        """
        orders_list = self.receive_orders_data()
        for order in orders_list:
            status_url = f"https://api.partner.market.yandex.ru/campaigns/23746359/orders/{order['order_id']}/status"

            payload = json.dumps(
                {
                    "order": {
                        "status": "PROCESSING",
                        "substatus": "READY_TO_SHIP",
                    }
                }

            )
            response_data = requests.request(
                "PUT", status_url, headers=yandex_headers_karavaev, data=payload)

    def receive_delivery_number(self):
        """
        YANDEXMARKET
        Определяет id поставки для подтверждения отгрузки.
        """
        url_delivery = 'https://api.partner.market.yandex.ru/campaigns/23746359/first-mile/shipments'

        date_for_delivery = datetime.now() + timedelta(days=1)
        date_for_delivery = date_for_delivery.strftime('%d-%m-%Y')
        payload = json.dumps({
            "dateFrom": date_for_delivery,
            "dateTo": date_for_delivery,
            "statuses": [
                "OUTBOUND_CREATED", "OUTBOUND_CONFIRMED",
                "OUTBOUND_READY_FOR_CONFIRMATION", "FINISHED"
            ]
        })

        response_delivery = requests.request(
            "PUT", url_delivery, headers=yandex_headers_karavaev, data=payload)
        shipments_list = json.loads(response_delivery.text)[
            'result']['shipments']
        if len(shipments_list) == 0:
            message_text = 'На завтра нет поставки Яндекс Маркета'
            bot.send_message(chat_id=CHAT_ID_ADMIN,
                             text=message_text, parse_mode='HTML')
        else:
            shipment_dict = {}
            shipment_id = shipments_list[0]['id']
            self.shipment_id = shipments_list[0]['id']
            shipment_dict['shipment_id'] = shipment_id
            return shipment_dict

    def received_info_about_delivery(self):
        """
        YANDEXMARKET.
        Получает информацию о предстоящей отгрузке.
        """
        shipment_data = self.receive_delivery_number()
        shipment_id = shipment_data['shipment_id']

        # shipment_id = 45554272
        url_info = f'https://api.partner.market.yandex.ru/campaigns/23746359/first-mile/shipments/{shipment_id}'

        response = requests.request(
            "GET", url_info, headers=yandex_headers_karavaev)
        info_main_data = json.loads(response.text)['result']
        orders_list = info_main_data['orderIds']
        shipment_data = {}
        shipment_data['shipment_id'] = shipment_id
        shipment_data['orders_list'] = orders_list

        return shipment_data

    def check_actual_orders(self):
        """
        YANDEXMARKET
        Проверяет все ордеры в поставке и исключает отмененнные
        """
        shipment_data = self.received_info_about_delivery()

        orders_info_list = []
        inner_info_dict = {}
        raw_orders_list = shipment_data['orders_list']
        for order in raw_orders_list:

            inner_info_list = []
            url_check = f'https://api.partner.market.yandex.ru/campaigns/23746359/orders/{order}'
            response = requests.request(
                "GET", url_check, headers=yandex_headers_karavaev)
            check_main_data = json.loads(response.text)['order']
            if check_main_data['status'] != 'CANCELLED':
                self.orders_list.append(order)
                for article in check_main_data['items']:
                    inner_article_list = {}
                    inner_article_list['seller_article'] = article['offerId']
                    inner_article_list['name'] = article['offerName']
                    inner_article_list['amount'] = article['count']

                    inner_info_list.append(inner_article_list)

                inner_info_dict[order] = inner_info_list

                orders_info_list.append(inner_info_dict)
        return inner_info_dict

    def approve_shipment(self):
        """
        YANDEXMARKET
        Подтверждение отгрузки
        """
        shipment_data = self.received_info_about_delivery()
        data = self.check_actual_orders()
        shipment_id = shipment_data['shipment_id']

        approve_url = f'https://api.partner.market.yandex.ru/campaigns/23746359/first-mile/shipments/{shipment_id}/confirm'
        payload_approve = json.dumps({
            "externalShipmentId": f'{shipment_id}',
            "orderIds": self.orders_list
        })
        response = requests.request(
            "POST", approve_url, headers=yandex_headers_karavaev, data=payload_approve)

    # def check_docs_for_shipment(self):
    #     """
    #     YANDEXMARKET
    #     Получает информацию о возможности печати ярлыков-наклеек для заказов в отгрузке
    #     """
    #     shipment_dict = self.receive_delivery_number()
    #     if shipment_dict:
    #         shipment_id = shipment_dict['shipment_id']
    #         check_url = f'https://api.partner.market.yandex.ru/campaigns/23746359/first-mile/shipments/{self.shipment_id}/orders/info'

    #         response_check = requests.request(
    #             "GET", check_url, headers=yandex_headers_karavaev)

    #         shipment_docs_dict = {}

    #         check_info = json.loads(response_check.text)['result']

    #         possible_for_print_list = check_info['orderIdsWithLabels']

    #         shipment_docs_dict['shipment_id'] = shipment_id
    #         shipment_docs_dict['orders_list'] = possible_for_print_list

    #         return shipment_docs_dict
    #         # else:
    #         #    print('не все этикетки готовы')
    #         #    time.sleep(300)
    #         #    self.check_docs_for_shipment()

    def saving_act(self):
        """
        YANDEXMARKET
        Сохраняет акт приема - передачи в PDF формате.
        """
        # self.shipment_id = 45554272
        url_act = f'https://api.partner.market.yandex.ru/campaigns/23746359/first-mile/shipments/{self.shipment_id}/act'

        response_act = requests.request(
            "GET", url_act, headers=yandex_headers_karavaev)

        # print(response_act.text)
        pdf_data = response_act.content  # замените на фактические входные данные
        folder_path = os.path.join(
            os.getcwd(), f'{self.main_save_folder_server}/yandex')
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        save_folder_docs = f'{folder_path}/YANDEX - ИП акт {self.date_for_files}.pdf'
        # сохранение PDF-файла
        with open(save_folder_docs, 'wb') as f:
            f.write(pdf_data)
        folder = (
            f'{self.dropbox_current_assembling_folder}/YANDEX - ИП акт {self.date_for_files}.pdf')
        with open(save_folder_docs, 'rb') as f:
            dbx_db.files_upload(f.read(), folder)

    def saving_tickets(self):
        """
        YANDEXMARKET
        Сохраняет этикетки в PDF формате.
        """
        orders_info_list = self.check_actual_orders()
        for order in self.orders_list:
            url_tickets = f'https://api.partner.market.yandex.ru/campaigns/23746359/orders/{order}/delivery/labels'
            response_tickets = requests.request(
                "GET", url_tickets, headers=yandex_headers_karavaev)

            pdf_data = response_tickets.content  # замените на фактические входные данные
            folder_path = os.path.join(
                os.getcwd(), f'{self.main_save_folder_server}/yandex/tickets')
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            save_folder_docs = f'{folder_path}/{order}.pdf'

            # сохранение PDF-файла
            with open(save_folder_docs, 'wb') as f:
                f.write(pdf_data)

        done_tickets_folder = os.path.join(
            os.getcwd(), f'{self.main_save_folder_server}/yandex/tickets/done')
        if not os.path.exists(done_tickets_folder):
            os.makedirs(done_tickets_folder)

        new_data_for_yandex_ticket(folder_path, orders_info_list)
        list_filenames = glob.glob(f'{done_tickets_folder}/*.pdf')
        folder_summary_file_name = f'{self.main_save_folder_server}/yandex/YANDEX - ИП этикетки {self.date_for_files}.pdf'
        merge_barcode_for_yandex_two_on_two(
            list_filenames, folder_summary_file_name)
        folder = (
            f'{self.dropbox_current_assembling_folder}/YANDEX - ИП акт {self.date_for_files}.pdf')
        with open(save_folder_docs, 'rb') as f:
            dbx_db.files_upload(f.read(), folder)

    def create_yandex_selection_sheet_pdf(self):
        """
        YANDEXMARKET
        Формирует файл подбора
        """
        date_for_files = datetime.now().strftime('%Y-%m-%d')

        main_shipment_data = self.check_actual_orders()
        number_of_departure_ya = main_shipment_data.keys()

        yandex_selection_sheet_xls = openpyxl.Workbook()

        create = yandex_selection_sheet_xls.create_sheet(
            title='pivot_list', index=0)
        create.page_setup.paperSize = create.PAPERSIZE_A4
        create.page_setup.orientation = create.ORIENTATION_PORTRAIT
        create.page_margins.left = 0.25
        create.page_margins.right = 0.25
        create.page_margins.top = 0.25
        create.page_margins.bottom = 0.25
        create.page_margins.header = 0.3
        create.page_margins.footer = 0.3

        sheet = yandex_selection_sheet_xls['pivot_list']
        sheet['A1'] = f'Лист подбора Яндекс Маркета {date_for_files}'
        font = Font(size=16)
        # Применяем стиль шрифта к ячейке с надписью
        sheet['A1'].font = font
        sheet.merge_cells('A1:D1')

        sheet['A3'] = 'Номер отправления'
        sheet['B3'] = 'Наименование товара'
        sheet['C3'] = 'Артикул'
        sheet['D3'] = 'Количество'

        al = Alignment(horizontal="center",
                       vertical="center", wrap_text=True)
        al2 = Alignment(vertical="center", wrap_text=True)
        thin = Side(border_style="thin", color="000000")
        thick = Side(border_style="medium", color="000000")
        pattern = PatternFill('solid', fgColor="fcff52")

        upd_number_of_departure_ya = []
        upd_product_name_ya = []
        upd_name_for_print_ya = []
        upd_amount_for_print_ya = []

        for key, value in main_shipment_data.items():
            for data in value:
                upd_number_of_departure_ya.append(key)
                upd_product_name_ya.append(data['name'])
                upd_name_for_print_ya.append(data['seller_article'])
                upd_amount_for_print_ya.append(data['amount'])

        for i in range(len(upd_number_of_departure_ya)):
            create.cell(
                row=i+4, column=1).value = upd_number_of_departure_ya[i]
            create.cell(row=i+4, column=2).value = upd_product_name_ya[i]
            create.cell(row=i+4, column=3).value = upd_name_for_print_ya[i]
            create.cell(
                row=i+4, column=4).value = upd_amount_for_print_ya[i]
        for i in range(3, len(upd_number_of_departure_ya)+4):
            for c in create[f'A{i}:D{i}']:
                c[0].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[1].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[2].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[3].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[3].alignment = al
                for j in range(4):
                    c[j].alignment = al
        create.column_dimensions['A'].width = 18
        create.column_dimensions['B'].width = 38
        create.column_dimensions['C'].width = 18
        create.column_dimensions['D'].width = 12
        name_for_file = f'{self.main_save_folder_server}/yandex/YANDEX - ИП лист подбора {self.date_for_files}'
        yandex_selection_sheet_xls.save(f'{name_for_file}.xlsx')

        xl = DispatchEx("Excel.Application")
        xl.DisplayAlerts = False
        folder_path = os.path.dirname(os.path.abspath(f'{name_for_file}.xlsx'))
        name_for_file = f'YANDEX - ИП лист подбора {self.date_for_files}'
        name_pdf_dropbox = f'YANDEX - ИП лист подбора {self.date_for_files}.pdf'
        wb = xl.Workbooks.Open(f'{folder_path}/{name_for_file}.xlsx')
        xl.CalculateFull()
        pythoncom.PumpWaitingMessages()
        try:
            wb.ExportAsFixedFormat(
                0, f'{folder_path}/{name_for_file}.pdf')
        except Exception as e:
            print(
                "Failed to convert in PDF format.Please confirm environment meets all the requirements  and try again")
        finally:
            wb.Close()
        # Сохраняем на DROPBOX
        with open(f'{folder_path}/{name_for_file}.pdf', 'rb') as f:
            dbx_db.files_upload(
                f.read(), f'{self.dropbox_current_assembling_folder}/{name_pdf_dropbox}.pdf')


clearning_folders()
yand = YandexMarketFbsMode()

# 1. Меняет статус ордеров
# yand.change_orders_status()
#
# 2. Формирует файл подбора
yand.create_yandex_selection_sheet_pdf()

# 3. Подтверждение отгрузки
# yand.approve_shipment()

# 4. Сохраняем акт.
yand.saving_act()

# 5. Сохраняем этикетки
# yand.saving_tickets()
