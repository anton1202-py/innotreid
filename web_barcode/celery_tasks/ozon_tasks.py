import json
import math
import os

import pandas as pd
import requests
import telegram
from celery_tasks.celery import app
from dotenv import load_dotenv

from .helpers_func import error_message, stream_dropbox_file

dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)

OZON_OOO_API_TOKEN = os.getenv('OZON_OOO_API_TOKEN')
OZON_OOO_CLIENT_ID = os.getenv('OZON_OOO_CLIENT_ID')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID_ADMIN = os.getenv('CHAT_ID_ADMIN')
bot = telegram.Bot(token=TELEGRAM_TOKEN)

API_KEY_WB = os.getenv('API_KEY_WB_IP')

headers = {
    'Client-Id': OZON_OOO_CLIENT_ID,
    'Api-Key': OZON_OOO_API_TOKEN,
    'Content-Type': 'application/json',
}


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


def request_info_stocks_data(last_id='', main_stock_data=None):
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

    response = requests.request("POST", url, headers=headers, data=payload)
    stocks_data = json.loads(response.text)['result']['items']
    for data in stocks_data:
        main_stock_data.append(data)

    if len(stocks_data) == 1000:
        request_info_stocks_data(json.loads(
            response.text)['result']['last_id'], main_stock_data)
    return main_stock_data


def product_id_list():
    """Выдает список списков product_id"""
    stocks_data = request_info_stocks_data()
    product_id_list = []
    for data in stocks_data:
        product_id_list.append(data['product_id'])
    return product_id_list


def sku_article_data():
    """Берет SKU FBS артикула по его offer_id
    Возвращает словарь вида {offer_id: sku}"""
    product_list = product_id_list()
    koef_product = math.ceil(len(product_list)//900)
    info_url = 'https://api-seller.ozon.ru/v2/product/info/list'
    main_info_dict = {}
    for i in range(koef_product+1):
        start_point = i*900
        finish_point = (i+1)*900
        big_info_list = product_list[
            start_point:finish_point]
        payload = json.dumps({
            "offer_id": [],
            "product_id": big_info_list
        })
        response = requests.request(
            "POST", info_url, headers=headers, data=payload)
        article_data = json.loads(response.text)['result']['items']
        for data in article_data:
            if data['fbs_sku'] != 0:
                main_info_dict[data['offer_id']] = data['fbs_sku']
            else:
                main_info_dict[data['offer_id']] = data['sku']
    return main_info_dict


def balance_on_fbs_night_stock():
    """Возвращет остаток на складе Иннотрейд Ночь"""
    main_info_dict = sku_article_data()
    sku_list = list(main_info_dict.values())
    koef_sku = math.ceil(
        len(sku_list)//400)
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
        response = requests.request("POST", url, headers=headers, data=payload)
        stocks_data = json.loads(response.text)['result']
        for data in stocks_data:
            if data['warehouse_id'] == 22676408482000:
                sku_stock_dict[data['product_id']] = data['present']
    return sku_stock_dict


def article_with_big_balance():
    """Функция ищет артикулы, остаток которых на складах FBO >= 20"""
    stocks_data = request_info_stocks_data()
    stop_list = create_stop_article_list()
    stock_night_dict = balance_on_fbs_night_stock()
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


@app.task
def fbs_balance_maker():
    """Обновляет остаток на FBS в зависимости от остатка на FBO складе"""
    try:
        warehouse_id = 22676408482000
        update_balance_url = 'https://api-seller.ozon.ru/v2/products/stocks'

        article_big_balance_dict, article_small_balance_dict = article_with_big_balance()

        # В ОЗОН стоит ограничение на 100 артикулов в запросе. На всякий случай сделал 90
        koef_small_balance = math.ceil(
            len(article_small_balance_dict.keys())//90)
        koef_big_balance = math.ceil(len(article_big_balance_dict.keys())//90)

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
                "POST", update_balance_url, headers=headers, data=payload)

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
                # print('Делаем остаток 100 на FBS', inner_request_dict['offer_id'])
                inner_request_dict['product_id'] = article_small_balance_dict[article]
                inner_request_dict['stock'] = 100
                inner_request_dict['warehouse_id'] = warehouse_id
                request_list.append(inner_request_dict)
            payload = json.dumps({
                "stocks": request_list
            })

            response = requests.request(
                "POST", update_balance_url, headers=headers, data=payload)
        message_text = f'Артикулы для обнуления остатков FBS: {list(article_big_balance_dict.keys())}'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message_text, parse_mode='HTML')
        message_text = f'Артикулы для увеличения остатков FBS: {list(article_small_balance_dict.keys())}'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message_text, parse_mode='HTML')
    except Exception as e:
        # обработка ошибки и отправка сообщения через бота
        message_text = error_message('fbs_balance_maker', fbs_balance_maker, e)
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message_text, parse_mode='HTML')
