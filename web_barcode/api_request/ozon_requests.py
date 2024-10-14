import json
import math
import os
import time
from datetime import datetime, timedelta
import traceback

import requests
import telegram
# from celery_tasks.celery import app
from dotenv import load_dotenv
from price_system.models import Articles, DesignUser
from price_system.supplyment import sender_error_to_tg

from api_request.common_func import api_retry_decorator
from web_barcode.constants_file import (CHAT_ID_ADMIN, TELEGRAM_TOKEN, bot,
                                        header_ozon_dict, header_wb_dict,
                                        header_yandex_dict,
                                        ozon_adv_client_access_id_dict,
                                        ozon_adv_client_secret_dict,
                                        ozon_api_token_dict,
                                        wb_headers_karavaev, wb_headers_ooo,
                                        yandex_business_id_dict)


@sender_error_to_tg
def ozon_sales_monthly_report(header, month, year, attempt=0):
    """Получаем данные по продажам с ОЗОН за предыдущий месяц"""
    url = f'https://api-seller.ozon.ru/v2/finance/realization'
    payload = json.dumps({
        "month": month,
        "year": year
    })
    response = requests.request(
        "POST", url, headers=header, data=payload)
    attempt += 1
    message = ''
    if attempt <= 50:
        if response.status_code == 200:
            all_data = json.loads(response.text)
            return all_data
        else:
            time.sleep(65)

            return ozon_sales_monthly_report(header, month, year, attempt)
    elif response.status_code == 403:
        message = f'статус код {response.status_code}. Доступ запрещен'
    elif response.status_code == 429:
        message = f'статус код {response.status_code}. Слишком много запросов'
    elif response.status_code == 401:
        message = f'статус код {response.status_code}. Не авторизован'
    else:
        message = f'статус код {response.status_code} у получения инфы всех артикулов ООО ВБ'

    if message:
        message = f'api_request.ozon_sales_monthly_report. {message}'
        bot.send_message(chat_id=CHAT_ID_ADMIN, text=message)


@sender_error_to_tg
def ozon_orders_daily_report(header, check_date, attempt=0):
    """Получаем данные по заказам с ОЗОН за позавчера"""
    url = "https://api-seller.ozon.ru/v1/analytics/data"
    payload = json.dumps({
        "date_from": check_date,
        "date_to": check_date,
        "metrics": [
            "revenue",
            "ordered_units"
        ],
        "dimension": [
            "sku"
        ],
        "limit": 1000,
        "offset": 0
    })
    response = requests.request("POST", url, headers=header, data=payload)
    attempt += 1
    message = ''
    if attempt <= 30:
        if response.status_code == 200:
            all_data = json.loads(response.text)
            return all_data
        else:
            time.sleep(65)
            return ozon_orders_daily_report(header, attempt)
    elif response.status_code == 403:
        message = f'статус код {response.status_code}. Доступ запрещен'
    elif response.status_code == 429:
        message = f'статус код {response.status_code}. Слишком много запросов'
    elif response.status_code == 401:
        message = f'статус код {response.status_code}. Не авторизован'
    else:
        message = f'статус код {response.status_code} у получения инфы заказов артикулов ОЗОН'
    if message:
        message = f'api_request.ozon_orders_daily_report {message}'
        bot.send_message(chat_id=CHAT_ID_ADMIN, text=message)


# =========== АКЦИИ ========== #
@api_retry_decorator
def ozon_actions_first_list(header):
    """
    Возвращает список акций с датами и временем проведения
    Максимум 10 запросов за 6 секунд
    """
    time.sleep(1)
    url = f'https://api-seller.ozon.ru/v1/actions'
    response = requests.request("GET", url, headers=header)
    return response


# @api_retry_decorator
def ozon_articles_in_action(header, action_number, limit=1000, offset=0, attempt=0, product_in_action=None):
    """
    Метод для получения списка товаров, которые могут 
    участвовать в акции, по её идентификатору.
    """
    try:
        if not product_in_action:
            product_in_action = []
        time.sleep(1)
        url = f'https://api-seller.ozon.ru/v1/actions/candidates'
        payload = json.dumps({
            "action_id": action_number,
            "limit": limit,
            "offset": offset
        })
        response = requests.request("POST", url, headers=header, data=payload)
        if response.status_code ==200:
            attempt += 1
            main_data = json.loads(response.text)['result']['products']
            for data in main_data:
                product_in_action.append(data)
            if len(main_data) == limit:
                offset = limit * attempt
                return ozon_articles_in_action(header, action_number, limit, offset, attempt, product_in_action)
            else:
                return product_in_action
        else:
            message = f'статус код {response.status_code}. "ozon_articles_in_action". {ozon_articles_in_action.__doc__}.'   
            if message:
                bot.send_message(chat_id=CHAT_ID_ADMIN,
                                 text=message[:4000])
    except Exception as e:
        tb_str = traceback.format_exc()
        message_error = (f'Ошибка в функции: <b>ozon_articles_in_action</b>\n'
                         f'<b>Функция выполняет</b>: {ozon_articles_in_action.__doc__}\n'
                         f'<b>Ошибка</b>\n: {e}\n\n'
                         f'<b>Техническая информация</b>:\n {tb_str}')
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message_error[:4000])


def add_ozon_articles_to_action(header, action_number, article_data_list):
    """
    Метод для получения списка товаров, которые могут 
    участвовать в акции, по её идентификатору.
    """
    time.sleep(1)
    url = f'https://api-seller.ozon.ru/v1/actions/products/activate'
    payload = json.dumps({
        "action_id": action_number,
        "products": article_data_list
    })
    print('article_data_list', article_data_list)
    response = requests.request("POST", url, headers=header, data=payload)
    print(action_number, response.status_code)
    print(action_number, response.text)

    return response
    

def del_articles_from_action(header, action_number, article_list):
    """
    Метод для удаления товаров из акции.
    """
    time.sleep(1)
    url = f'https://api-seller.ozon.ru/v1/actions/products/deactivate'
    payload = json.dumps({
        "action_id": action_number,
        "product_ids": article_list
    })
    response = requests.request("POST", url, headers=header, data=payload)
    print(response.status_code)
    return response
    
# =========== КОНЕЦ АКЦИИ ========== #