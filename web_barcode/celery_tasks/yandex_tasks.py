import json
import math
import os
import time
from datetime import datetime

import pandas as pd
import requests
import telegram
from celery_tasks.celery import app
from dotenv import load_dotenv

from .helpers_func import error_message, stream_dropbox_file

dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID_ADMIN = os.getenv('CHAT_ID_ADMIN')
bot = telegram.Bot(token=TELEGRAM_TOKEN)

YANDEX_OOO_KEY = os.getenv('YANDEX_OOO_KEY')
YANDEX_IP_KEY = os.getenv('YANDEX_IP_KEY')

CHAT_ID_EU = os.getenv('CHAT_ID_EU')
CHAT_ID_AN = os.getenv('CHAT_ID_AN')

YANDEX_OOO_FBY_CAMPAIGN_ID = os.getenv('YANDEX_OOO_FBY_CAMPAIGN_ID')
YANDEX_OOO_FBS_CAMPAIGN_ID = os.getenv('YANDEX_OOO_FBS_CAMPAIGN_ID')
YANDEX_IP_FBY_CAMPAIGN_ID = os.getenv('YANDEX_IP_FBY_CAMPAIGN_ID')
YANDEX_IP_FBS_CAMPAIGN_ID = os.getenv('YANDEX_IP_FBS_CAMPAIGN_ID')

yandex_headers_ooo = {
    'Authorization': YANDEX_OOO_KEY,
}
yandex_headers_ip = {
    'Authorization': YANDEX_IP_KEY,
}
tg_accounts = [CHAT_ID_EU, CHAT_ID_AN]


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


def sku_data_function(ur_headers, fby_campaign_id, nextPageToken='', main_sku_data=None):
    """Возвращает список sku продавца, которые готовы к продаже и остаток которых = 0"""
    stop_list = create_stop_article_list()
    if main_sku_data is None:
        main_sku_data = []
    url = f'https://api.partner.market.yandex.ru/campaigns/{fby_campaign_id}/offers?limit=200&page_token={nextPageToken}'
    payload = json.dumps({
        "statuses": ["PUBLISHED", "NO_STOCKS"]
    })
    response = requests.request(
        "POST", url, headers=ur_headers, data=payload)
    sku_main_data = json.loads(response.text)['result']

    sku_article_data = sku_main_data['offers']

    for article in sku_article_data:
        if article['offerId'] not in stop_list:
            main_sku_data.append(article['offerId'])
    if sku_main_data['paging']:
        sku_data_function(ur_headers, fby_campaign_id, sku_main_data['paging']
                          ['nextPageToken'], main_sku_data)
    return main_sku_data


def request_info_fby_stocks_data(ur_headers, fby_campaign_id):
    """
    Функция делает запросы на эндпоинт:
    https://api.partner.market.yandex.ru/campaigns/fby_campaign_id/stats/skus
    и возвращает словарь с данными по количеству товара на складе FBY ООО
    Возвращает словарь main_stock_data_dict {Артикул: Остаток}
    """
    # Словарь с данными {Артикул: Остаток}
    main_stock_data_dict = {}
    # Список артикулов в магазине.
    seller_sku_list = sku_data_function(ur_headers, fby_campaign_id)
    koef_product = math.ceil(len(seller_sku_list)//400)
    url = f"https://api.partner.market.yandex.ru/campaigns/{fby_campaign_id}/stats/skus"
    for i in range(koef_product+1):
        start_point = i*400
        finish_point = (i+1)*400
        sku_list = seller_sku_list[
            start_point:finish_point]
        payload = json.dumps({
            "shopSkus": sku_list
        })
        response = requests.request(
            "POST", url, headers=ur_headers, data=payload)
        sku_data = json.loads(response.text)['result']['shopSkus']
        for sku in sku_data:
            count = 0
            try:
                for stock in sku['warehouses']:
                    for article_count in stock['stocks']:
                        if article_count['type'] == 'AVAILABLE':
                            count += article_count['count']
                main_stock_data_dict[sku['shopSku']] = count
            except:
                main_stock_data_dict[sku['shopSku']] = 0
    return main_stock_data_dict


def fbs_stocks_data(ur_headers, fbs_campaign_id, nextPageToken='', fbs_sku_data=None):
    """Создает и возвращает словарь с данными fbs_sku_data {артикул: остаток_fbs}"""
    stop_list = create_stop_article_list()
    if fbs_sku_data == None:
        fbs_sku_data = {}
    url = f'https://api.partner.market.yandex.ru/campaigns/{fbs_campaign_id}/offers/stocks?limit=200&page_token={nextPageToken}'
    payload = json.dumps({
        "withTurnover": False,
        "archived": False
    })
    response = requests.request(
        "POST", url, headers=ur_headers, data=payload)
    fbs_main_data = json.loads(response.text)['result']
    sku_article_data = fbs_main_data['warehouses']
    for article in sku_article_data:
        for stocks in article['offers']:
            count = 0
            if stocks['offerId'] not in stop_list:
                for stocks_count in stocks['stocks']:
                    if stocks_count['type'] == 'AVAILABLE':
                        count = stocks_count['count']
                if stocks['offerId'] in fbs_sku_data.keys():
                    fbs_sku_data[stocks['offerId']
                                 ] = fbs_sku_data[stocks['offerId']] + count
                else:
                    fbs_sku_data[stocks['offerId']] = count
    if fbs_main_data['paging']:
        fbs_stocks_data(ur_headers, fbs_campaign_id,
                        fbs_main_data['paging']['nextPageToken'], fbs_sku_data)
    return fbs_sku_data


def create_action_lists(ur_headers, fbs_campaign_id, fby_campaign_id):
    """Создает списки для обнуления FBS остатков и для их увеличения"""
    fby_stock_dict = request_info_fby_stocks_data(ur_headers, fby_campaign_id)
    fbs_stock_dict = fbs_stocks_data(ur_headers, fbs_campaign_id)

    article_for_null_list = []
    article_for_greate_list = []
    for key_fby, value_fby in fby_stock_dict.items():
        if key_fby in fbs_stock_dict.keys():
            if value_fby > 2 and fbs_stock_dict[key_fby] != 0:
                article_for_null_list.append(key_fby)
            elif value_fby <= 2 and fbs_stock_dict[key_fby] < 50:
                article_for_greate_list.append(key_fby)
    return article_for_null_list, article_for_greate_list


def fbs_balance_maker(ur_headers, fbs_campaign_id, fby_campaign_id):
    """Обновляет остаток на FBS в зависимости от остатка на FBY складе"""
    try:
        update_balance_url = f'https://api.partner.market.yandex.ru/campaigns/{fbs_campaign_id}/offers/stocks'
        time_now = datetime.now()
        now = time_now.strftime('%Y-%m-%dT%H:%M:%SZ')
        article_for_null_list, article_for_greate_list = create_action_lists(
            ur_headers, fbs_campaign_id, fby_campaign_id)
        # Обнуляем остатки на FBS
        for article in article_for_null_list:
            payload = json.dumps({
                "skus": [
                    {
                        "sku": article,
                        "warehouseId": 250643,
                        "items": [
                            {
                                "count": 0,
                                "type": "FIT",
                                "updatedAt": now
                            }
                        ]
                    }
                ]
            })
            response = requests.request(
                "PUT", update_balance_url, headers=ur_headers, data=payload)
        # Увеличиваем остатки на FBS
        for article in article_for_greate_list:
            payload = json.dumps({
                "skus": [
                    {
                        "sku": article,
                        "warehouseId": 250643,
                        "items": [
                            {
                                "count": 100,
                                "type": "FIT",
                                "updatedAt": now
                            }
                        ]
                    }
                ]
            })
            response = requests.request(
                "PUT", update_balance_url, headers=ur_headers, data=payload)
        if len(article_for_null_list) != 0:
            message_text = f'Артикулы для обнуления остатков YANDEX FBS: {article_for_null_list}'
            for chat_id in tg_accounts:
                print(
                    f'Артикулы для обнуления остатков YANDEX FBS: {article_for_null_list}')
                bot.send_message(chat_id=chat_id,
                                 text=message_text, parse_mode='HTML')
        if len(article_for_greate_list) != 0:
            message_text = f'Артикулы для увеличения остатков YANDEX FBS: {article_for_greate_list}'
            print(
                f'Артикулы для увеличения остатков YANDEX FBS: {article_for_greate_list}')
            for chat_id in tg_accounts:
                bot.send_message(chat_id=chat_id,
                                 text=message_text, parse_mode='HTML')
    except Exception as e:
        # обработка ошибки и отправка сообщения через бота
        message_text = error_message('fbs_balance_maker', fbs_balance_maker, e)
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message_text, parse_mode='HTML')


@app.task
def fbs_balance_updater():
    """Вызывает функции для работы с остатками ФБС на ООО и ИП"""
    try:
        fbs_balance_maker(yandex_headers_ooo,
                          YANDEX_OOO_FBS_CAMPAIGN_ID, YANDEX_OOO_FBY_CAMPAIGN_ID)
        time.sleep(60)
        fbs_balance_maker(yandex_headers_ip,
                          YANDEX_IP_FBS_CAMPAIGN_ID, YANDEX_IP_FBY_CAMPAIGN_ID)
    except Exception as e:
        # обработка ошибки и отправка сообщения через бота
        message_text = error_message('fbs_balance_maker', fbs_balance_maker, e)
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message_text, parse_mode='HTML')
