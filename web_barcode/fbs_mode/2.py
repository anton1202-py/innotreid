import base64
import glob
import io
import json
import os
import re
import shutil
import time
from collections import Counter
from contextlib import closing
from datetime import datetime
from pathlib import Path

import dropbox
import img2pdf
import pandas as pd
import pdfplumber
import requests
from barcode import Code128
from barcode.writer import ImageWriter
from dotenv import load_dotenv
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
from PyPDF3 import PdfFileReader, PdfFileWriter
from PyPDF3.pdf import PageObject
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

version = 'w1.0'

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


def atoi(text):
    """Для сортировки файлов в списках для присоединения"""
    return int(text) if text.isdigit() else text


def natural_keys(text):
    """
    alist.sort(key=natural_keys) sorts in human order
    """
    return [atoi(c) for c in re.split(r'(\d+)', text)]


def qrcode_order():
    """
    WILDBERRIES.
    Функция добавляет сборочные задания по их id
    в созданную поставку и получает qr стикер каждого
    задания и сохраняет его в папку
    """
    order_list = [1534937658, 1535269830, 1535436413]
    # Создаем qr коды добавленных ордеров.
    for order in order_list:
        ticket_url = 'https://suppliers-api.wildberries.ru/api/v3/orders/stickers?type=png&width=40&height=30'
        payload_ticket = json.dumps({"orders": [order]})
        response_ticket = requests.request(
            "POST", ticket_url, headers=wb_headers_karavaev, data=payload_ticket)
        # Расшифровываю ответ, чтобы сохранить файл этикетки задания
        ticket_data = json.loads(response_ticket.text)[
            "stickers"][0]["file"]
        # Узнаю стикер сборочного задания и помещаю его в словарь с данными для
        # листа подбора
        sticker_code_first_part = json.loads(response_ticket.text)[
            "stickers"][0]["partA"]
        sticker_code_second_part = json.loads(response_ticket.text)[
            "stickers"][0]["partB"]
        sticker_code = f'{sticker_code_first_part} {sticker_code_second_part}'

        # декодируем строку из base64 в бинарные данные
        binary_data = base64.b64decode(ticket_data)
        # создаем объект изображения из бинарных данных
        img = Image.open(io.BytesIO(binary_data))
        # сохраняем изображение в файл
        folder_path = os.path.join(
            os.getcwd(), "fbs_mode/data_for_barcodes/qrcode_folder")
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        img.save(
            f"{folder_path}/{order}.png")


# qrcode_order()


def qrcode_print_for_products():
    """
    Создает QR коды в необходимом формате и добавляет к ним артикул и его название 
    из excel файла. Сравнивает цифры из файла с QR кодами и цифры из excel файла.
    Таким образом находит артикулы и названия.
    Входящие файлы:
    filename - название файла с qr-кодами. Для создания промежуточной папки.
    """
    dir = 'fbs_mode/data_for_barcodes/qrcode_folder/'
    if not os.path.exists(dir):
        os.makedirs(dir)
    os.chmod(dir, 0o777)

    filelist = glob.glob(os.path.join(dir, "*.png"))
    print('FILELIST', filelist)
    filelist.sort(key=natural_keys)
    i = 0
    font1 = ImageFont.truetype("arial.ttf", size=40)
    font2 = ImageFont.truetype("arial.ttf", size=90)

    filename = 'fbs_mode/data_for_barcodes/qrcode_folder/cache_dir_3/'
    if not os.path.exists(filename):
        os.makedirs(filename)
    os.chmod(filename, 0o777)

    for file in filelist:
        path = Path(file)
        file_name = str(os.path.basename(path).split('.')[0])
        name_data = file_name.split('\\')
        print('name_data', name_data)
        sticker_data = name_data[0]
        barcode_size = [img2pdf.in_to_pt(2.759), img2pdf.in_to_pt(1.95)]
        layout_function = img2pdf.get_layout_fun(barcode_size)
        im = Image.new('RGB', (660, 466), color=('#ffffff'))
        image1 = Image.open(file)
        draw_text = ImageDraw.Draw(im)

        # Вставляем qr код в основной фон
        im.paste(image1, (70, 100))
        draw_text.text(
            (90, 80),
            f'{sticker_data}',
            font=font1,
            fill=('#000'), stroke_width=1
        )
        im.save(
            f'{filename}/{file_name}.png')
        pdf = img2pdf.convert(
            f'{filename}/{file_name}.png', layout_fun=layout_function)
        with open(f'{filename}/{file_name}.pdf', 'wb') as f:
            f.write(pdf)
        i += 1
    pdf_filenames_qrcode = glob.glob(f'{filename}/*.pdf')
    pdf_filenames_qrcode.sort(key=natural_keys)
    filelist.clear()

    # filelist = glob.glob(os.path.join(filename, "*"))
    # for f in filelist:
    #    try:
    #        os.remove(f)
    #    except Exception:
    #        print('')
    return pdf_filenames_qrcode


qrcode_print_for_products()
