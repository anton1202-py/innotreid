import importlib
import inspect
import json
import os
import traceback

import requests
import telegram
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)


API_KEY_WB_IP = os.getenv('API_KEY_WB_IP')
YANDEX_IP_KEY = os.getenv('YANDEX_IP_KEY')
API_KEY_OZON_KARAVAEV = os.getenv('API_KEY_OZON_KARAVAEV')
CLIENT_ID_OZON_KARAVAEV = os.getenv('CLIENT_ID_OZON_KARAVAEV')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID_ADMIN = os.getenv('CHAT_ID_ADMIN')

bot = telegram.Bot(token=TELEGRAM_TOKEN)

wb_headers_karavaev = {
    'Content-Type': 'application/json',
    'Authorization': API_KEY_WB_IP
}

ozon_headers_karavaev = {
    'Api-Key': API_KEY_OZON_KARAVAEV,
    'Content-Type': 'application/json',
    'Client-Id': CLIENT_ID_OZON_KARAVAEV
}

yandex_headers_karavaev = {
    'Authorization': YANDEX_IP_KEY,
}


def uppercase(func):
    def wrapper():
        try:
            func()
        except Exception as e:
            tb_str = traceback.format_exc()
            message_error = (f'Ошибка в функции: <b>{func.__name__}</b>\n'
                             f'<b>Функция выполняет</b>: {func.__doc__}\n'
                             f'<b>Ошибка</b>\n: {e}\n\n'
                             f'<b>Техническая информация</b>:\n {tb_str}')
            bot.send_message(chat_id=CHAT_ID_ADMIN,
                             text=message_error, parse_mode='HTML')
    return wrapper


# @uppercase
def wb_articles_list():
    """Получаем массив арткулов с ценами и скидками для ВБ"""
    n = 1 + '23'
    print(n)


def doc_type(function_path):
    module_name, function_name = function_path.rsplit('.', 1)
    # Динамически импортируем модуль
    module = importlib.import_module(module_name)

    # Получаем объект функции
    function = getattr(module, function_name)

    # Получаем документацию функции
    docstring = inspect.getdoc(function)

    return docstring


print(doc_type('fbs_mode.tasks.ip_friday_task'))
