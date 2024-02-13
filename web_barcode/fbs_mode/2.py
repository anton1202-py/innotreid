import base64
import glob
import io
import json
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
# from celery_tasks.celery import app
from dotenv import load_dotenv
from msoffice2pdf import convert
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


def stream_dropbox_file(path):
    _, res = dbx_db.files_download(path)
    with closing(res) as result:
        byte_data = result.content
        return io.BytesIO(byte_data)


def create_ozone_selection_sheet_pdf(fbs_ozon_common_data_buils_dict):
    """OZON. Создает лист подбора для OZON"""
    dropbox_current_assembling_folder = '/DATABASE/beta/ИП'
    main_save_folder_server = 'fbs_mode/data_for_barcodes'
    file_add_name = 'ИП'

    sorted_data_buils_dict = dict(
        sorted(fbs_ozon_common_data_buils_dict.items(), key=lambda x: x[0][-6:]))
    number_of_departure_oz = sorted_data_buils_dict.keys()
    ozone_selection_sheet_xls = openpyxl.Workbook()
    create = ozone_selection_sheet_xls.create_sheet(
        title='pivot_list', index=0)
    sheet = ozone_selection_sheet_xls['pivot_list']
    sheet['A1'] = 'Номер отправления'
    sheet['B1'] = 'Наименование товара'
    sheet['C1'] = 'Артикул'
    sheet['D1'] = 'Количество'
    sheet.row_dimensions[0].auto_size = True
    al = Alignment(horizontal="center",
                   vertical="center", wrap_text=True)
    al2 = Alignment(vertical="center", wrap_text=True)
    thin = Side(border_style="thin", color="000000")
    thick = Side(border_style="medium", color="000000")
    pattern = PatternFill('solid', fgColor="fcff52")
    upd_number_of_departure_oz = []
    upd_product_name_oz = []
    upd_name_for_print_oz = []
    upd_amount_for_print_oz = []
    for key, value in sorted_data_buils_dict.items():
        for data in value:
            upd_number_of_departure_oz.append(key)
            upd_product_name_oz.append(data['Наименование'])
            upd_name_for_print_oz.append(data['Артикул продавца'])
            upd_amount_for_print_oz.append(data['Количество'])
    create.row_dimensions[2].height = 180
    create.column_dimensions['A'].width = 18
    create.column_dimensions['B'].width = 38
    create.column_dimensions['C'].width = 18
    create.column_dimensions['D'].width = 10
    for i in range(len(upd_number_of_departure_oz)):
        create.cell(
            row=i+2, column=1).value = upd_number_of_departure_oz[i]
        wrapped_lines = textwrap.wrap(create.cell(
            row=i+2, column=1).value, width=18)
        num_lines = len(wrapped_lines)
        row_height = 12 * num_lines
        print('row_height', row_height)
        create.cell(row=i+2, column=2).value = upd_product_name_oz[i]

        create.cell(row=i+2, column=3).value = upd_name_for_print_oz[i]
        create.cell(
            row=i+2, column=4).value = upd_amount_for_print_oz[i]
    for i in range(1, len(upd_number_of_departure_oz)+2):
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
            create.row_dimensions[i].height = row_height
            for j in range(3):
                c[j].alignment = al2

    folder_path_docs = os.path.join(
        os.getcwd(), f'{main_save_folder_server}/ozon_docs')
    if not os.path.exists(folder_path_docs):
        os.makedirs(folder_path_docs)
    name_for_file = f'{folder_path_docs}/selection_sheet'
    ozone_selection_sheet_xls.save(f'{name_for_file}.xlsx')
    w_b2 = load_workbook(f'{name_for_file}.xlsx')
    source_page2 = w_b2.active
    number_of_departure_oz = source_page2['A']
    amount_for_print_oz = source_page2['D']
    for i in range(1, len(number_of_departure_oz)+2):
        if i < len(number_of_departure_oz)-1:
            for c in source_page2[f'A{i+1}:D{i+1}']:
                if (number_of_departure_oz[i].value == number_of_departure_oz[i+1].value
                        and number_of_departure_oz[i].value != number_of_departure_oz[i-1].value):
                    c[0].border = Border(
                        top=thick, left=thick, bottom=thin, right=thin)
                    c[1].border = Border(
                        top=thick, left=thin, bottom=thin, right=thin)
                    c[2].border = Border(
                        top=thick, left=thin, bottom=thin, right=thin)
                    c[3].border = Border(
                        top=thick, left=thin, bottom=thin, right=thick)
                    for j in range(4):
                        c[j].fill = pattern
                if (number_of_departure_oz[i].value == number_of_departure_oz[i+1].value
                        and number_of_departure_oz[i].value == number_of_departure_oz[i-1].value):
                    c[0].border = Border(
                        top=thin, left=thick, bottom=thin, right=thin)
                    c[1].border = Border(
                        top=thin, left=thin, bottom=thin, right=thin)
                    c[2].border = Border(
                        top=thin, left=thin, bottom=thin, right=thin)
                    c[3].border = Border(
                        top=thin, left=thin, bottom=thin, right=thick)
                    for j in range(4):
                        c[j].fill = pattern
                elif (number_of_departure_oz[i].value != number_of_departure_oz[i+1].value
                        and number_of_departure_oz[i].value == number_of_departure_oz[i-1].value):
                    c[0].border = Border(
                        top=thin, left=thick, bottom=thick, right=thin)
                    c[1].border = Border(
                        top=thin, left=thin, bottom=thick, right=thin)
                    c[2].border = Border(
                        top=thin, left=thin, bottom=thick, right=thin)
                    c[3].border = Border(
                        top=thin, left=thin, bottom=thick, right=thick)
                    for j in range(4):
                        c[j].fill = pattern
                if amount_for_print_oz[i].value > 1:
                    c[0].border = Border(
                        top=thick, left=thick, bottom=thick, right=thin)
                    c[1].border = Border(
                        top=thick, left=thin, bottom=thick, right=thin)
                    c[2].border = Border(
                        top=thick, left=thin, bottom=thick, right=thin)
                    c[3].border = Border(
                        top=thick, left=thin, bottom=thick, right=thick)
                    for j in range(4):
                        c[j].fill = pattern
    w_b2.save(f'{name_for_file}.xlsx')
    wb = load_workbook(f'{name_for_file}.xlsx')

    # Выбираем активный лист
    ws = wb.active

    # Получаем высоту строки и ширину столбца для конкретной ячейки (например, A1)
    cell = ws["A2"]
    row_height = ws.row_dimensions[cell.row].height
    column_width = ws.column_dimensions[cell.column_letter].width

    print(f"Высота строки: {row_height}")
    print(f"Ширина столбца: {column_width}")
    path_file = os.path.abspath(f'{name_for_file}.xlsx')
    only_file_name = os.path.splitext(os.path.basename(path_file))[0]
    folder_path = os.path.dirname(os.path.abspath(path_file))

    output = convert(source=path_file, output_dir=folder_path, soft=0)

    now_date = datetime.now().strftime(("%d.%m %H-%M"))
    folder_xls = (
        f'{dropbox_current_assembling_folder}/OZON - {file_add_name} лист подбора {now_date}.xlsx')
    folder = (
        f'{dropbox_current_assembling_folder}/OZON - {file_add_name} {now_date} лист подбора.pdf')
    with open(output, 'rb') as f:
        dbx_db.files_upload(f.read(), folder)
    with open(path_file, 'rb') as f:
        dbx_db.files_upload(f.read(), folder_xls)


fbs_ozon_common_data_buils_dict = {'88215326-0005-1': [{'Артикул продавца': 'V451', 'Наименование': 'Ночник "Куки Синобу"', 'Количество': 1}], '88215343526-0005-1': [{'Артикул продавца': 'V4512', 'Наименование': 'Ночник "Куки Синобу sfsfkhsfksdhfsdkflhsdfksdfbskfjsdhfklsdhfsdkfhsdfs"', 'Количество': 1}], '882s15343526-0005-1': [{'Артикул продавца': 'V4512',
                                                                                                                                                                                                                                                                                                                                           'Наименование': 'Ночник "Куки Синобу sfsfkhsfksdhfsdkflhsdfksdfbskfjsdhfklsdhfsdkfhsdfs"', 'Количество': 1}], '882135343526-0005-1': [{'Артикул продавца': 'V4512', 'Наименование': 'Ночник "Куки Синобу sfsfkhsfksdhfsdkflhsdfksdfbskfjsdhfklsdhfsdkfhsdfs"', 'Количество': 1}], '884215343526-0005-1': [{'Артикул продавца': 'V4512', 'Наименование': 'Ночник "Куки Синобу sfsfkhsfksdhfsdkflhsdfksdfbskfjsdhfklsdhfsdkfhsdfs"', 'Количество': 1}]}
create_ozone_selection_sheet_pdf(fbs_ozon_common_data_buils_dict)
