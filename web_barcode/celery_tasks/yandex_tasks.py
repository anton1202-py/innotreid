import json
import math
import os
import time
from datetime import datetime

import pandas as pd
import requests
import telegram
from api_request.yandex_requests import fbs_warehouse_article_balance
from celery_tasks.celery import app
from dotenv import load_dotenv
from price_system.supplyment import sender_error_to_tg

from web_barcode.constants_file import (CHAT_ID_ADMIN, CHAT_ID_AN, CHAT_ID_EU,
                                        bot, header_yandex_dict,
                                        ur_lico_list_for_yandex_fbs_balance,
                                        yandex_fbs_campaign_id_dict,
                                        yandex_fbs_warehouse_id_dict,
                                        yandex_fby_campaign_id_dict)

from .helpers_func import error_message, stream_dropbox_file

tg_accounts = [CHAT_ID_EU, CHAT_ID_AN]

warehouse_yandex_market_fbs_dict = {

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


@sender_error_to_tg
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


@sender_error_to_tg
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


@sender_error_to_tg
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


@sender_error_to_tg
def fbs_balance_maker(ur_lico, header, fbs_campaign_id, fby_campaign_id):
    """Обновляет остаток на FBS в зависимости от остатка на FBY складе"""
    try:
        article_for_null_list, article_for_greate_list = create_action_lists(
            header, fbs_campaign_id, fby_campaign_id)

        # Обнуляем остатки на FBS
        warehouse_id = yandex_fbs_warehouse_id_dict[ur_lico]
        for article in article_for_null_list:
            fbs_warehouse_article_balance(
                article, warehouse_id, 0, header, fbs_campaign_id)
        # Увеличиваем остатки на FBS
        for article in article_for_greate_list:
            fbs_warehouse_article_balance(
                article, warehouse_id, 100, header, fbs_campaign_id)
        if len(article_for_null_list) != 0:
            message_text = f'Артикулы для обнуления остатков YANDEX FBS: {article_for_null_list}'

        if len(article_for_greate_list) != 0:
            message_text = f'Артикулы для увеличения остатков YANDEX FBS: {article_for_greate_list}'

    except Exception as e:
        # обработка ошибки и отправка сообщения через бота
        message_text = error_message('fbs_balance_maker', fbs_balance_maker, e)
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message_text, parse_mode='HTML')


@app.task
def fbs_balance_updater():
    """Вызывает функции для работы с остатками ФБС на ООО и ИП"""
    try:
        for ur_lico in ur_lico_list_for_yandex_fbs_balance:
            fbs_balance_maker(ur_lico, header_yandex_dict[ur_lico],
                              yandex_fbs_campaign_id_dict[ur_lico],
                              yandex_fby_campaign_id_dict[ur_lico])
            time.sleep(60)
    except Exception as e:
        # обработка ошибки и отправка сообщения через бота
        message_text = error_message('fbs_balance_maker', fbs_balance_maker, e)
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message_text, parse_mode='HTML')
