import datetime
import json
import math
import os
import time
import traceback
from datetime import datetime

import pandas as pd
import requests
import telegram
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.reader.excel import load_workbook
from openpyxl.styles import Alignment, Border, PatternFill, Side
from price_system.supplyment import sender_error_to_tg

from web_barcode.constants_file import (CHAT_ID_ADMIN, TELEGRAM_TOKEN,
                                        header_ozon_dict, header_wb_data_dict,
                                        header_wb_dict, header_yandex_dict,
                                        wb_headers_karavaev, wb_headers_ooo,
                                        yandex_business_id_dict)

bot = telegram.Bot(token=TELEGRAM_TOKEN)


def api_retry_decorator(func):
    def wrapper(*args, **kwargs):
        message = ''
        try:
            response = func(*args, **kwargs)
            for attempt in range(30):  # Попробуем выполнить запрос не более 50 раз
                response = func(*args, **kwargs)
                if response.status_code == 200:
                    json_response = json.loads(response.text)
                    return json_response
                elif response.status_code == 204:
                    message = ''
                elif response.status_code == 403:
                    message = f'статус код {response.status_code}. {func.__name__}. {func.__doc__}. Доступ запрещен'
                elif response.status_code == 429:
                    message = f'статус код {response.status_code}. {func.__name__}. {func.__doc__}. Слишком много запросов'
                elif response.status_code == 401:
                    message = f'статус код {response.status_code}. {func.__name__}. {func.__doc__}. Не авторизован'
                elif response.status_code == 404:
                    message = f'статус код {response.status_code}. {func.__name__}. {func.__doc__}. Страница не существует'
                else:
                    time.sleep(10)  # Ждем 1 секунду перед повторным запросом
                if message:
                    bot.send_message(chat_id=CHAT_ID_ADMIN,
                                     text=message[:4000])
                    return []

            message = f'статус код {response.status_code}. {func.__name__}. {func.__doc__}.'
            if message:
                bot.send_message(chat_id=CHAT_ID_ADMIN,
                                 text=message[:4000])
                return []
        except Exception as e:
            tb_str = traceback.format_exc()
            message_error = (f'Ошибка в функции: <b>{func.__name__}</b>\n'
                             f'<b>Функция выполняет</b>: {func.__doc__}\n'
                             f'<b>Ошибка</b>\n: {e}\n\n'
                             f'<b>Техническая информация</b>:\n {tb_str}')
            bot.send_message(chat_id=CHAT_ID_ADMIN,
                             text=message_error[:4000])
    return wrapper
