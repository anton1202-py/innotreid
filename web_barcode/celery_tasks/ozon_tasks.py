import json
import math
import os
import time

import pandas as pd
import requests
import telegram
from celery_tasks.celery import app
from dotenv import load_dotenv
from price_system.supplyment import sender_error_to_tg

from .helpers_func import stream_dropbox_file

dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)

OZON_OOO_API_TOKEN = os.getenv('OZON_OOO_API_TOKEN')
OZON_OOO_CLIENT_ID = os.getenv('OZON_OOO_CLIENT_ID')

OZON_IP_API_TOKEN = os.getenv('OZON_IP__API_TOKEN')
OZON_IP_CLIENT_ID = os.getenv('OZON_IP_CLIENT_ID')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID_ADMIN = os.getenv('CHAT_ID_ADMIN')
CHAT_ID_EU = os.getenv('CHAT_ID_EU')
CHAT_ID_AN = os.getenv('CHAT_ID_AN')

tg_accounts = [CHAT_ID_EU, CHAT_ID_AN]
bot = telegram.Bot(token=TELEGRAM_TOKEN)

API_KEY_WB = os.getenv('API_KEY_WB_IP')


headers_ooo = {
    'Client-Id': OZON_OOO_CLIENT_ID,
    'Api-Key': OZON_OOO_API_TOKEN,
    'Content-Type': 'application/json',
}

headers_ip = {
    'Client-Id': OZON_IP_CLIENT_ID,
    'Api-Key': OZON_IP_API_TOKEN,
    'Content-Type': 'application/json',
}

ur_lico_dict = {
    'ООО Иннотрейд': headers_ooo,
    'ИП Караваев': headers_ip
}

working_storage = {
    'ООО Иннотрейд': 22676408482000,
    'ИП Караваев': 1020000089903000
}


@sender_error_to_tg
def create_stop_article_list():
    """Формирует список стоп артикулов у которых не нужно корректировать остатки на FBS"""
    DROPBOX_STOP_FILE_ADDRESS = '/DATABASE/список сопоставления.xlsx'
    dropbox_read_stop_file = stream_dropbox_file(DROPBOX_STOP_FILE_ADDRESS)
    dropbox_info_stop_file = pd.read_excel(dropbox_read_stop_file)
    dropbox_data_stop_file = pd.DataFrame(
        dropbox_info_stop_file, columns=['Артикул', 'Баркод товара'])
    stop_dropbox_article_list = dropbox_data_stop_file['Артикул'].to_list()
    stop_dropbox_barcode_list = dropbox_data_stop_file['Баркод товара'].to_list(
    )

    stop_list = []

    for code in range(len(stop_dropbox_barcode_list)):
        if str(stop_dropbox_barcode_list[code]) != 'nan':
            stop_list.append(stop_dropbox_article_list[code])
    return stop_list


@sender_error_to_tg
def request_info_stocks_data(header, last_id='', main_stock_data=None):
    """
    Функция делает запросы на эндпоинт:
    https://api-seller.ozon.ru/v3/product/info/stocks
    и возвращает список со словарями о данных по количеству на складе
    """
    if main_stock_data is None:
        main_stock_data = []
    url = "https://api-seller.ozon.ru/v3/product/info/stocks"

    payload = json.dumps({
        "filter": {
            "offer_id": [],
            "product_id": [],
            "visibility": "ALL"
        },
        "last_id": last_id,
        "limit": 1000
    })

    response = requests.request("POST", url, headers=header, data=payload)
    stocks_data = json.loads(response.text)['result']['items']
    for data in stocks_data:
        main_stock_data.append(data)

    if len(stocks_data) == 1000:
        request_info_stocks_data(header, json.loads(
            response.text)['result']['last_id'], main_stock_data)
    return main_stock_data


@sender_error_to_tg
def product_id_list(header):
    """Выдает список списков product_id"""
    stocks_data = request_info_stocks_data(header)
    product_id_list = []
    for data in stocks_data:
        product_id_list.append(data['product_id'])
    return product_id_list


@sender_error_to_tg
def sku_article_data(header):
    """Берет SKU FBS артикула по его offer_id
    Возвращает словарь вида {offer_id: sku}"""
    product_list = product_id_list(header)
    koef_product = math.ceil(len(product_list)/900)
    info_url = 'https://api-seller.ozon.ru/v2/product/info/list'
    main_info_dict = {}
    for i in range(koef_product):
        start_point = i*900
        finish_point = (i+1)*900
        big_info_list = product_list[
            start_point:finish_point]
        payload = json.dumps({
            "offer_id": [],
            "product_id": big_info_list
        })
        response = requests.request(
            "POST", info_url, headers=header, data=payload)
        article_data = json.loads(response.text)['result']['items']
        for data in article_data:
            if data['sku'] != 0:
                main_info_dict[data['offer_id']] = data['sku']
            else:
                if data['fbs_sku'] != 0:
                    main_info_dict[data['offer_id']] = data['fbs_sku']
                elif data['fbo_sku'] != 0:
                    main_info_dict[data['offer_id']] = data['fbo_sku']
                else:
                    continue
    return main_info_dict


@sender_error_to_tg
def balance_on_fbs_night_stock(header, storage):
    """Возвращет остаток на складе Иннотрейд Ночь"""
    main_info_dict = sku_article_data(header)
    sku_list = list(main_info_dict.values())
    koef_sku = math.ceil(
        len(sku_list)/400)
    sku_stock_dict = {}
    url = "https://api-seller.ozon.ru/v1/product/info/stocks-by-warehouse/fbs"
    for i in range(koef_sku):
        start_point = i*400
        finish_point = (i+1)*400
        data_sku_list = sku_list[
            start_point:finish_point]
        payload = json.dumps({
            "sku": data_sku_list
        })
        response = requests.request("POST", url, headers=header, data=payload)
        stocks_data = json.loads(response.text)['result']
        for data in stocks_data:
            if data['warehouse_id'] == storage:
                sku_stock_dict[data['product_id']] = data['present']
    return sku_stock_dict


@sender_error_to_tg
def article_with_big_balance(header, storage):
    """Функция ищет артикулы, остаток которых на складах FBO >= 20"""
    stocks_data = request_info_stocks_data(header)
    stop_list = create_stop_article_list()
    stock_night_dict = balance_on_fbs_night_stock(header, storage)
    article_big_balance_dict = {}
    article_small_balance_dict = {}

    for article_data in stocks_data:
        fbo_value = next(
            (dictionary["present"] for dictionary in article_data['stocks'] if dictionary["type"] == "fbo"), None)
        if article_data['offer_id'] not in stop_list:
            if article_data['product_id'] in stock_night_dict.keys():
                stock_night = stock_night_dict[article_data['product_id']]
                if fbo_value < 5 and stock_night < 50:
                    article_small_balance_dict[article_data['offer_id']
                                               ] = article_data['product_id']
                elif fbo_value >= 20 and stock_night != 0:
                    article_big_balance_dict[article_data['offer_id']
                                             ] = article_data['product_id']
    return article_big_balance_dict, article_small_balance_dict


@sender_error_to_tg
def fbs_balance_maker(header, storage):
    """Обновляет остаток на FBS в зависимости от остатка на FBO складе"""
    warehouse_id = storage
    update_balance_url = 'https://api-seller.ozon.ru/v2/products/stocks'
    article_big_balance_dict, article_small_balance_dict = article_with_big_balance(
        header, storage)
    # В ОЗОН стоит ограничение на 100 артикулов в запросе. На всякий случай сделал 90
    koef_small_balance = math.ceil(
        len(article_small_balance_dict.keys())/90)
    koef_big_balance = math.ceil(len(article_big_balance_dict.keys())/90)
    for i in range(koef_big_balance+1):
        # Лист для запроса в эндпоинту ОЗОНа
        request_list = []
        start_point = i*90
        finish_point = (i+1)*90
        big_info_list = list(article_big_balance_dict.keys())[
            start_point:finish_point]
        for article in big_info_list:
            inner_request_dict = {}
            inner_request_dict['offer_id'] = article
            inner_request_dict['product_id'] = article_big_balance_dict[article]
            inner_request_dict['stock'] = 0
            inner_request_dict['warehouse_id'] = warehouse_id
            request_list.append(inner_request_dict)
        payload = json.dumps({
            "stocks": request_list
        })
        response = requests.request(
            "POST", update_balance_url, headers=header, data=payload)
    for i in range(koef_small_balance+1):
        # Лист для запроса в эндпоинту ОЗОНа
        request_list = []
        start_point = i*90
        finish_point = (i+1)*90
        small_info_list = list(article_small_balance_dict.keys())[
            start_point:finish_point]
        for article in small_info_list:
            inner_request_dict = {}
            inner_request_dict['offer_id'] = article
            inner_request_dict['product_id'] = article_small_balance_dict[article]
            inner_request_dict['stock'] = 100
            inner_request_dict['warehouse_id'] = warehouse_id
            request_list.append(inner_request_dict)
        payload = json.dumps({
            "stocks": request_list
        })
        response = requests.request(
            "POST", update_balance_url, headers=header, data=payload)
    if len(list(article_big_balance_dict.keys())) != 0:
        message_text = f'Артикулы для обнуления остатков ОЗОН FBS: {list(article_big_balance_dict.keys())}'
        for chat_id in tg_accounts:
            bot.send_message(chat_id=chat_id,
                             text=message_text, parse_mode='HTML')
    if len(list(article_small_balance_dict.keys())) != 0:
        message_text = f'Артикулы для увеличения остатков ОЗОН FBS: {list(article_small_balance_dict.keys())}'
        for chat_id in tg_accounts:
            bot.send_message(chat_id=chat_id,
                             text=message_text, parse_mode='HTML')


@sender_error_to_tg
@app.task
def fbs_balance_maker_for_all_company():
    """Обновляет остаток на FBS в зависимости от остатка на FBO складе для ООО и ИП"""
    for ur_lico, header in ur_lico_dict.items():
        storage = working_storage[ur_lico]
        fbs_balance_maker(header, storage)
        time.sleep(60)
