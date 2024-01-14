import base64
import io
import json
import os
from contextlib import closing
from datetime import datetime
from io import BytesIO

import dropbox
import img2pdf
import pandas as pd
import requests
from barcode import Code128
from barcode.writer import ImageWriter
from dotenv import load_dotenv
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont

version = 'w1.0'
delivery_date = datetime.today().strftime("%d.%m.%Y %H-%M-%S")
dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)

REFRESH_TOKEN_DB = os.getenv('REFRESH_TOKEN_DB')
APP_KEY_DB = os.getenv('APP_KEY_DB')
APP_SECRET_DB = os.getenv('APP_SECRET_DB')
API_KEY_WB_IP = os.getenv('API_KEY_WB_IP')

dbx_db = dropbox.Dropbox(oauth2_refresh_token=REFRESH_TOKEN_DB,
                         app_key=APP_KEY_DB,
                         app_secret=APP_SECRET_DB)

wb_headers_karavaev = {
    'Content-Type': 'application/json',
    'Authorization': API_KEY_WB_IP
}

ozon_headers_karavaev = {
    'Api-Key': os.getenv('API_KEY_OZON_KARAVAEV'),
    'Content-Type': 'application/json',
    'Client-Id': os.getenv('CLIENT_ID_OZON_KARAVAEV')
}


def stream_dropbox_file(path):
    _, res = dbx_db.files_download(path)
    with closing(res) as result:
        byte_data = result.content
        return io.BytesIO(byte_data)


def qrcode_order(self):
    """
    WILDBERRIES.
    Функция добавляет сборочные задания по их id
    в созданную поставку и получает qr стикер каждого
    задания и сохраняет его в папку
    """
    # try:
    # Добавляем заказы в поставку
    # for order in self.article_id_dict.keys():
    #    add_url = f'https://suppliers-api.wildberries.ru/api/v3/supplies/{self.supply_id}/orders/{order}'
    #    response_add_orders = requests.request(
    #        "PATCH", add_url, headers=wb_headers_karavaev)
    # Создаем qr коды добавленных ордеров.
    for order in self.article_id_dict.keys():
        ticket_url = 'https://suppliers-api.wildberries.ru/api/v3/orders/stickers?type=png&width=58&height=40'
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
        self.selection_dict[order].append(sticker_code)
        # декодируем строку из base64 в бинарные данные
        binary_data = base64.b64decode(ticket_data)
        # создаем объект изображения из бинарных данных
        img = Image.open(BytesIO(binary_data))
        # сохраняем изображение в файл
        img.save(
            f"web_barcode/fbs_mode/data_for_barcodes/qrcode_folder/{order} {self.article_id_dict[order]}.png")
    # except Exception as e:
    #    # обработка ошибки и отправка сообщения через бота
    #    message_text = error_message('qrcode_order', self.qrcode_order, e)
    #    bot.send_message(chat_id=CHAT_ID_ADMIN,
    #                     text=message_text, parse_mode='HTML')


def create_delivery():
    url_data = 'https://suppliers-api.wildberries.ru/api/v3/supplies'
    hour = datetime.now().hour
    delivery_name = f"Поставка {delivery_date}"
    if hour >= 18 or hour <= 6:
        delivery_name = f'Ночь {delivery_date}'
    else:
        delivery_name = f'День {delivery_date}'
    payload = json.dumps(
        {
            "name": delivery_name
        }
    )
    # Из этой переменной достать ID поставки
    response_data = requests.request(
        "POST", url_data, headers=wb_headers_karavaev, data=payload)
    # print(response_data)
    global supply_id
    supply_id = json.loads(response_data.text)['id']
    print(supply_id)


def qrcode_supply():
    """
    WILDBERRIES.
    Функция добавляет поставку в доставку, получает QR код поставки
    и преобразует этот QR код в необходимый формат.
    """
    # try:
    # Переводим поставку в доставку
    # url_to_supply = f'https://suppliers-api.wildberries.ru/api/v3/supplies/{self.supply_id}/deliver'
    # response_to_supply = requests.request(
    #    "PATCH", url_to_supply, headers=wb_headers_karavaev)
    supply_id = 'WB-GI-71656568'
    # Получаем QR код поставки:
    url_supply_qrcode = f"https://suppliers-api.wildberries.ru/api/v3/supplies/{supply_id}/barcode?type=png"
    response_supply_qrcode = requests.request(
        "GET", url_supply_qrcode, headers=wb_headers_karavaev)
    # Создаем QR код поставки
    qrcode_base64_data = json.loads(
        response_supply_qrcode.text)["file"]
    # декодируем строку из base64 в бинарные данные
    binary_data = base64.b64decode(qrcode_base64_data)
    # создаем объект изображения из бинарных данных
    img = Image.open(BytesIO(binary_data))
    # сохраняем изображение в файл
    img.save(
        f"fbs_mode/data_for_barcodes/qrcode_supply/{supply_id}.png")
    # except Exception as e:
    #    # обработка ошибки и отправка сообщения через бота
    #    message_text = error_message(
    #        'qrcode_supply', self.qrcode_supply, e)
    #    bot.send_message(chat_id=CHAT_ID_ADMIN,
    #                     text=message_text, parse_mode='HTML')


# create_delivery()
qrcode_supply()
