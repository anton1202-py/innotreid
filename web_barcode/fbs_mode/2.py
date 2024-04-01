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
# from price_system.supplyment import sender_error_to_tg
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


# @sender_error_to_tg
def merge_barcode_for_yandex_two_on_two(list_filenames, folder_summary_file_name):
    with open(list_filenames[0], "rb") as f:
        input1 = PdfFileReader(f, strict=False)
        # Создаем новую страницу
        page1 = input1.getPage(0)
        # Задаем максимальную ширину страницы.
        # Почему-то всегда берет самую длинную сторону в качестве ширины
        total_width = max([page1.mediaBox.upperRight[0]*(2)])
        # Задаем максимальную высоту страницы.
        # Почему-то всегда берет самую короткую сторону в качестве длины
        total_height = max([page1.mediaBox.upperRight[1]*(2)])
        # Горизонтальный размер страницы
        horiz_size = page1.mediaBox.upperRight[0]
        # Вертикальный размер страницы
        vertic_size = page1.mediaBox.upperRight[1]
        # Создаем объект записи конечного файла
        output = PdfFileWriter()
        # Присваиваем имя конечного файла
        file_name = folder_summary_file_name

        # Создаем страницу конечного файла
        new_page = PageObject.createBlankPage(
            file_name, total_width, total_height)
        # Размещаем нулевой элемент на первой странице
        new_page.mergeTranslatedPage(page1, 0, 0)
        # При добавлении страницы разворачиваем ее на 90 градусов.
        # Потому что длина берется всегда с длинной координаты, в у нас файл вертикальный.
        output.addPage(new_page.rotateClockwise(90))
        # Узнает из скольки страниц файл нам нужен
        page_amount = (len(list_filenames) // 4)
        if len(list_filenames) % 4 > 0:
            page_amount = page_amount + 1
        pages_names = []
        for p in range(1, page_amount):
            p = PageObject.createBlankPage(
                file_name, total_width, total_height)
            # При добавлении всех страниц переворачиваем их на 90 градусов, как первую.
            output.addPage(p.rotateClockwise(90))
            # Добавляем к новому файлу каждую страницу в цикле
            pages_names.append(p)
        for i in range(0, len(list_filenames)):
            with open(list_filenames[i], "rb") as bb:
                # Коэффициент счетчика страниц
                m = i // 4
                # Вертикальный коэффициент. Равен либо 0, либо 1.
                # Совпадает с остатком от деления на 2 номера файла
                n = i % 2
                # Горизонтальный коэффициент.
                k = (i // 2) - 2 * m
                # Размещаем файлы на первой странице.
                if i < 4:
                    new_page.mergeTranslatedPage(
                        PdfFileReader(bb,
                                      strict=False).getPage(0),
                        horiz_size*(k),
                        vertic_size*(n))
                # Размещаем файлы на всех последующих страницах.
                elif i >= 4:
                    (pages_names[m-1]).mergeTranslatedPage(
                        PdfFileReader(bb,
                                      strict=False).getPage(0),
                        horiz_size*(k),
                        vertic_size*(n))
                output.write(open(file_name, "wb"))
        f.close()


list_filenames = glob.glob(
    'web_barcode/fbs_mode/data_for_barcodes/yandex/*.pdf')
folder_summary_file_name = f'web_barcode/fbs_mode/data_for_barcodes/yandex/YANDEX - этикетки.pdf'

merge_barcode_for_yandex_two_on_two(list_filenames, folder_summary_file_name)
