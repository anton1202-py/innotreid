import datetime
import json
import math
import os
import traceback
from datetime import date, datetime

import requests
import telegram
from django.http import FileResponse, HttpResponse, JsonResponse
from dotenv import load_dotenv
from openpyxl import Workbook
from openpyxl.reader.excel import load_workbook
from openpyxl.styles import Alignment, Border, PatternFill, Side

from .models import ArticleGroup, Articles, Groups

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
bot = telegram.Bot(token=TELEGRAM_TOKEN)


def sender_error_to_tg(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            tb_str = traceback.format_exc()
            message_error = (f'Ошибка в функции: <b>{func.__name__}</b>\n'
                             f'<b>Функция выполняет</b>: {func.__doc__}\n'
                             f'<b>Ошибка</b>\n: {e}\n\n'
                             f'<b>Техническая информация</b>:\n {tb_str}')
            bot.send_message(chat_id=CHAT_ID_ADMIN,
                             text=message_error, parse_mode='HTML')
    return wrapper


def excel_creating_mod(data):
    """Создает и скачивает excel файл"""
    # Создаем DataFrame из данных
    wb = Workbook()
    # Получаем активный лист
    ws = wb.active

    # Заполняем лист данными
    for row, item in enumerate(data, start=2):
        ws.cell(row=row, column=1, value=str(item.common_article))
        ws.cell(row=row, column=2, value=str(item.group))
    # Устанавливаем заголовки столбцов
    ws.cell(row=1, column=1, value='Артикул')
    ws.cell(row=1, column=2, value='Группа')

    al = Alignment(horizontal="center",
                   vertical="center")
    al_left = Alignment(horizontal="left",
                        vertical="center")
    al2 = Alignment(vertical="center", wrap_text=True)
    thin = Side(border_style="thin", color="000000")
    thick = Side(border_style="medium", color="000000")
    pattern = PatternFill('solid', fgColor="fcff52")

    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 10

    for i in range(len(data)+1):
        for c in ws[f'A{i+1}:I{i+1}']:
            for i in range(9):
                c[i].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[i].alignment = al_left

    # Сохраняем книгу Excel в память
    response = HttpResponse(content_type='application/xlsx')
    name = f'Articles_groups_{datetime.now().strftime("%Y.%m.%d")}.xlsx'
    file_data = 'attachment; filename=' + name
    response['Content-Disposition'] = file_data
    wb.save(response)

    return response


def excel_compare_table(data):
    """Импортирует в excel таблицу сверки"""
    # Создаем DataFrame из данных
    wb = Workbook()
    # Получаем активный лист
    ws = wb.active

    # Заполняем лист данными
    for row, item in enumerate(data, start=2):
        ws.cell(row=row, column=1, value=str(item.common_article))
        ws.cell(row=row, column=2, value=str(item.status))
        ws.cell(row=row, column=3, value=str(item.company))

        ws.cell(row=row, column=4, value=str(item.wb_seller_article))
        ws.cell(row=row, column=5, value=str(item.wb_barcode))
        ws.cell(row=row, column=6, value=str(item.wb_nomenclature))

        ws.cell(row=row, column=7, value=str(item.ozon_seller_article))
        ws.cell(row=row, column=8, value=str(item.ozon_barcode))
        ws.cell(row=row, column=9, value=str(item.ozon_product_id))
        ws.cell(row=row, column=10, value=str(item.ozon_sku))
        ws.cell(row=row, column=11, value=str(item.ozon_fbo_sku_id))
        ws.cell(row=row, column=12, value=str(item.ozon_fbs_sku_id))

        ws.cell(row=row, column=13, value=str(item.yandex_seller_article))
        ws.cell(row=row, column=14, value=str(item.yandex_barcode))
        ws.cell(row=row, column=15, value=str(item.yandex_sku))

    # Устанавливаем заголовки столбцов
    ws.cell(row=1, column=1, value='Общий артикул')
    ws.cell(row=1, column=2, value='Статус')
    ws.cell(row=1, column=3, value='Компания')

    ws.cell(row=1, column=4, value='WB артикул поставщика')
    ws.cell(row=1, column=5, value='WB баркод')
    ws.cell(row=1, column=6, value='WB номенклатура')

    ws.cell(row=1, column=7, value='OZON артикул поставщика')
    ws.cell(row=1, column=8, value='OZON баркод')
    ws.cell(row=1, column=9, value='OZON PRODUCT_ID')
    ws.cell(row=1, column=10, value='OZON SKU')
    ws.cell(row=1, column=11, value='OZON FBO SKU ID')
    ws.cell(row=1, column=12, value='OZON FBS SKU ID')

    ws.cell(row=1, column=13, value='YANDEX артиукл поставщика')
    ws.cell(row=1, column=14, value='YANDEX баркод')
    ws.cell(row=1, column=15, value='YANDEX SKU')

    al = Alignment(horizontal="center",
                   vertical="center")
    al_left = Alignment(horizontal="left",
                        vertical="center")
    al2 = Alignment(vertical="center", wrap_text=True)
    thin = Side(border_style="thin", color="000000")
    thick = Side(border_style="medium", color="000000")
    pattern = PatternFill('solid', fgColor="fcff52")

    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 15
    ws.column_dimensions['G'].width = 15
    ws.column_dimensions['H'].width = 15
    ws.column_dimensions['I'].width = 15
    ws.column_dimensions['J'].width = 15
    ws.column_dimensions['K'].width = 15
    ws.column_dimensions['L'].width = 15
    ws.column_dimensions['M'].width = 15
    ws.column_dimensions['N'].width = 15
    ws.column_dimensions['O'].width = 15

    for i in range(len(data)+1):
        for c in ws[f'A{i+1}:O{i+1}']:
            for i in range(15):
                c[i].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[i].alignment = al_left

    # Сохраняем книгу Excel в память
    response = HttpResponse(content_type='application/xlsx')
    name = f'Article_table_{datetime.now().strftime("%Y.%m.%d")}.xlsx'
    file_data = 'attachment; filename=' + name
    response['Content-Disposition'] = file_data
    wb.save(response)
    return response


def excel_import_data(xlsx_file):
    """Импортирует данные о группе артикула из Excel"""
    workbook = load_workbook(filename=xlsx_file, read_only=True)
    worksheet = workbook.active
    # Читаем файл построчно и создаем объекты.
    for row in range(1, len(list(worksheet.rows))):
        if list(worksheet.rows)[row][1].value == None or list(worksheet.rows)[row][1].value == 'None':
            article = ArticleGroup.objects.get(
                common_article=Articles.objects.get(common_article=list(worksheet.rows)[row][0].value))
            article.group = None
            article.save()
        else:
            new_obj = ArticleGroup.objects.filter(
                common_article=Articles.objects.get(
                    common_article=list(worksheet.rows)[row][0].value)
            ).update(group=Groups.objects.get(name=list(worksheet.rows)[row][1].value))


def wb_price_changer(info_list: list):
    """Изменяет цену входящего списка артикулов на WB"""
    url = 'https://discounts-prices-api.wb.ru/api/v2/upload/task'
    payload = json.dumps({"data": info_list})
    response_data = requests.request(
        "POST", url, headers=wb_headers_karavaev, data=payload)


def wilberries_price_change(articles_list: list, price: int, discount: int):
    """Изменяет цену на артикулы Wildberries"""
    koef_articles = math.ceil(len(articles_list)/1000)
    for i in range(koef_articles):
        data_for_change = []
        start_point = i*1000
        finish_point = (i+1)*1000
        data_articles_list = articles_list[
            start_point:finish_point]
        for article in data_articles_list:
            if article != None:
                inner_data_dict = {
                    "nmId": article,
                    "price": price,
                    "discount": discount
                }
                data_for_change.append(inner_data_dict)
        wb_price_changer(data_for_change)


def ozon_price_changer(info_list: list):
    """Изменяет цену входящего списка артикулов на OZON"""
    url = 'https://api-seller.ozon.ru/v1/product/import/prices'
    payload = json.dumps({"prices": info_list})

    response_data = requests.request(
        "POST", url, headers=ozon_headers_karavaev, data=payload)


def ozon_price_change(articles_list: list, price: float, min_price: float, old_price=0):
    """Изменяет цену на артикулы OZON"""
    koef_articles = math.ceil(len(articles_list)/1000)
    for i in range(koef_articles):
        data_for_change = []
        start_point = i*1000
        finish_point = (i+1)*1000
        data_articles_list = articles_list[
            start_point:finish_point]
        for article in data_articles_list:
            if article != None:
                inner_data_dict = {
                    "auto_action_enabled": "UNKNOWN",
                    "currency_code": "RUB",
                    "min_price": str(min_price),
                    "offer_id": "",
                    "old_price": str(old_price),
                    "price": str(price),
                    "price_strategy_enabled": "UNKNOWN",
                    "product_id": article
                }
                data_for_change.append(inner_data_dict)
        ozon_price_changer(data_for_change)


def yandex_price_changer(info_list: list):
    """Изменяет цену входящего списка артикулов на OZON"""
    url = 'https://api.partner.market.yandex.ru/businesses/3345369/offer-prices/updates'
    payload = json.dumps({"offers": info_list})
    response_data = requests.request(
        "POST", url, headers=yandex_headers_karavaev, data=payload)


def yandex_price_change(articles_list: list, price: float, old_price=0):
    """Изменяет цену на артикулы YANDEX"""
    koef_articles = math.ceil(len(articles_list)/500)
    for i in range(koef_articles):
        data_for_change = []
        start_point = i*500
        finish_point = (i+1)*500
        data_articles_list = articles_list[
            start_point:finish_point]
        for article in data_articles_list:
            if article != None:
                inner_data_dict = {
                    "offerId": article,
                    "price": {
                        "value": price,
                        "currencyId": "RUR",
                        "discountBase": old_price
                    }
                }
                data_for_change.append(inner_data_dict)
        yandex_price_changer(data_for_change)
