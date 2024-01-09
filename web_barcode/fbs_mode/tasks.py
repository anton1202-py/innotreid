import base64
import glob
import io
import json
import math
import os
import shutil
import time
from collections import Counter
from contextlib import closing
from datetime import datetime
from io import BytesIO
from pathlib import Path

import dropbox
import img2pdf
import openpyxl
import pandas as pd
import psycopg2
import pythoncom
import requests
import win32com.client as win32
from barcode import Code128
from barcode.writer import ImageWriter
from dotenv import load_dotenv
from helpers import (print_barcode_to_pdf2, qrcode_print_for_products,
                     special_design_dark, special_design_light,
                     supply_qrcode_to_standart_view)
from openpyxl import Workbook, load_workbook
from openpyxl.drawing import image
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from PIL import Image, ImageDraw, ImageFont
from PyPDF3 import PdfFileReader, PdfFileWriter
from PyPDF3.pdf import PageObject
from sqlalchemy import create_engine
from win32com.client import DispatchEx

version = 'w1.0'

# Загрузка переменных окружения из файла .env
dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)

REFRESH_TOKEN_DB = os.getenv('REFRESH_TOKEN_DB')
APP_KEY_DB = os.getenv('APP_KEY_DB')
APP_SECRET_DB = os.getenv('APP_SECRET_DB')
API_KEY_WB_IP = os.getenv('API_KEY_WB_IP')

wb_headers_karavaev = {
    'Content-Type': 'application/json',
    'Authorization': API_KEY_WB_IP
}

dbx_db = dropbox.Dropbox(oauth2_refresh_token=REFRESH_TOKEN_DB,
                         app_key=APP_KEY_DB,
                         app_secret=APP_SECRET_DB)

delivery_date = datetime.today().strftime("%d.%m.%Y %H-%M-%S")


def stream_dropbox_file(path):
    _, res = dbx_db.files_download(path)
    with closing(res) as result:
        byte_data = result.content
        return io.BytesIO(byte_data)

# Использование переменных окружения


def common_barcode_design(dict_barcode_print):
    """
    dict_barcode_print - словарь с данными для штрихкода {артикул: [название светильника, штрихкод]}
    """
    UR_LICO_DATA = '/DATABASE/web_barcode_data/helper_files/Печать Караваев.xlsx'
    ur_lico_data = stream_dropbox_file(UR_LICO_DATA)

    df = pd.read_excel(ur_lico_data, header=None)
    value_a1 = df.iloc[0, 0]  # значение ячейки A1
    value_a2 = df.iloc[1, 0]  # значение ячейки A2
    value_a3 = df.iloc[2, 0]  # значение ячейки A3
    value_a4 = df.iloc[3, 0]  # значение ячейки A4
    value_a5 = df.iloc[4, 0]  # значение ячейки A5
    value_a6 = df.iloc[5, 0]  # значение ячейки A6

    # Задаем размер штрихкода
    barcode_size = [img2pdf.in_to_pt(2.759), img2pdf.in_to_pt(1.95)]
    layout_function = img2pdf.get_layout_fun(barcode_size)

    font = ImageFont.truetype("arial.ttf", size=50)
    font2 = ImageFont.truetype("arial.ttf", size=60)
    font3 = ImageFont.truetype("arial.ttf", size=120)
    font_version = ImageFont.truetype("arial.ttf", size=35)

    current_date = datetime.now().strftime("%d.%m.%Y")
    EAC_FILE = '/DATABASE/web_barcode_data/programm_data/eac.png'

    metadata, response = dbx_db.files_download(EAC_FILE)
    if not os.path.exists('web_barcode/fbs_mode/data_for_barcodes/cache_dir/'):
        os.makedirs('web_barcode/fbs_mode/data_for_barcodes/cache_dir/')
    with open('web_barcode/fbs_mode/data_for_barcodes/eac.png', 'wb') as eac_file:
        eac_file.write(response.content)

        # Создание самого штрихкода
    for key, value in dict_barcode_print.items():
        render_options = {
            "module_width": 1,
            "module_height": 35,
            "font_size": 20,
            "text_distance": 8,
            "quiet_zone": 8
        }
        barcode = Code128(
            f'{str(value[1])[:13]}',
            writer=ImageWriter()
        ).render(render_options)
        im = Image.new('RGB', (1980, 1400), color=('#000000'))
        image1 = Image.open('web_barcode/fbs_mode/data_for_barcodes/eac.png')
        draw_text = ImageDraw.Draw(im)
        # Длина подложки
        w_width = round(im.width/2)
        # Длина штрихкода
        w = round(barcode.width/2)
        # Расположение штрихкода по центру
        position = w_width - w
        # Вставляем штрихкод в основной фон
        im.paste(barcode, ((w_width - w), 250))
        # Вставляем EAC в основной фон
        im.paste(image1, (1505, 1028))
        draw_text.text(
            (position, 150),
            f'{value[0]}\n',
            font=font2,
            fill=('#ffffff'), stroke_width=1
        )
        draw_text.text(
            (position, barcode.height+270),
            f'{key}\n',
            font=font3,
            fill=('#ffffff'), stroke_width=1
        )
        draw_text.text(
            (position, barcode.height+410),
            f'{value_a1}\n'
            f'{value_a2}{current_date}\n'
            f'{value_a3} {value_a4}\n'
            f'{value_a5}\n'
            f'{value_a6}',
            font=font,
            fill=('#ffffff')
        )
        draw_text.text(
            (1780, 70),
            version,
            font=font_version,
            fill=('#ffffff')
        )
        im.save(f'web_barcode/fbs_mode/data_for_barcodes/cache_dir/{key}.png')
        im.close()
        pdf = img2pdf.convert(
            f'web_barcode/fbs_mode/data_for_barcodes/cache_dir/{key}.png',
            layout_fun=layout_function)
        with open(f'web_barcode/fbs_mode/data_for_barcodes/cache_dir/{key}.pdf', 'wb') as f:
            f.write(pdf)


def design_barcodes_dict_spec(names_for_print_barcodes, dict_barcode_print):
    """
    Создает дизайн штрихкода. Входящие файлы:
    names_for_print_barcodes - список всех артикулов для печати (получаем из файла).
    dict_barcode_print - словарь с информацией об артикуле: {артикул_продавца: [наименование, баркод]}
    sheet - лист excel с юр. данными для печати на штрихкоде (ООО или ИП).
    """
    SPECIAL_TICKETS_FILE_NAME = '/DATABASE/Специальные этикетки.xlsx'
    special_tickets_file = stream_dropbox_file(SPECIAL_TICKETS_FILE_NAME)
    special_tickets_data = pd.read_excel(special_tickets_file)

    special_tickets_data_file = pd.DataFrame(
        special_tickets_data, columns=['Артикул продавца', 'Цвет фона'])

    list_article_from_special_tickets_file = special_tickets_data_file['Артикул продавца'].to_list(
    )
    list_ticketcolor_from_special_tickets_file = special_tickets_data_file['Цвет фона'].to_list(
    )
    special_dict = {}

    for i in range(len(list_article_from_special_tickets_file)):
        special_dict[list_article_from_special_tickets_file[i]
                     ] = list_ticketcolor_from_special_tickets_file[i]

    names_for_print_barcodes_helper = []
    for i in names_for_print_barcodes:
        names_for_print_barcodes_helper.append(i)

    light_special_dict = {}
    dark_special_dict = {}
    dict_barcode_print = dict(sorted(dict_barcode_print.items()))

    for i in dict_barcode_print.keys():
        if i in special_dict.keys():
            if special_dict[i] == 'светлый' or special_dict[i] == 'Светлый':
                light_special_dict[i] = dict_barcode_print[i]
            elif special_dict[i] == 'темный' or special_dict[i] == 'Темный':
                dark_special_dict[i] = dict_barcode_print[i]

    if light_special_dict:
        for i in light_special_dict.keys():
            del dict_barcode_print[i]
    if dark_special_dict:
        for i in dark_special_dict.keys():
            del dict_barcode_print[i]

    # Вызывае функцию для печати обычных этикеток
    common_barcode_design(dict_barcode_print)

    # Проверяем на данные спец словари, если они не пустые, вызываем функции
    # для печати спец этикеток
    if light_special_dict:
        special_design_light(light_special_dict)

    if dark_special_dict:
        special_design_dark(dark_special_dict)


def list_for_print_create(amount_articles):
    """
    Функция создает список с полными именами файлов, которые нужно объединить
    amount_articles - словарь с данными {артикул_продавца: количество}
    """
    qrcode_list = qrcode_print_for_products()
    pdf_filenames = glob.glob(
        'web_barcode/fbs_mode/data_for_barcodes/cache_dir/*.pdf')
    list_pdf_file_ticket_for_complect = []
    if amount_articles:
        for j in pdf_filenames:
            while amount_articles[str(Path(j).stem)] > 0:
                list_pdf_file_ticket_for_complect.append(j)
                amount_articles[str(Path(j).stem)] -= 1
        for file in qrcode_list:
            list_pdf_file_ticket_for_complect.append(file)
        # Определяем число qr кодов для поставки.
        amount_of_supply_qrcode = math.ceil(
            len(list_pdf_file_ticket_for_complect)/20)
        print('list_pdf_file_ticket_for_complect',
              list_pdf_file_ticket_for_complect)
        print('amount_of_supply_qrcode', amount_of_supply_qrcode)
        outer_list = []  # Внешний список для процесса сортировки
        for i in list_pdf_file_ticket_for_complect:
            # Разделяю полное название файла на путь к файлу и имя файла
            # Оказывается в python знаком \ отделяется последняя папка перед файлом
            # А все внешние отделяются знаком /
            new_name = i.split('\\')
            full_new_name = []  # Список с полным именени файла после разделения
            # Имена QR кодов у меня составные. Состоят из нескольких слов с пробелами
            # В этом цикле разделяю имена из предыдущих списков по пробелу.
            for j in new_name:
                split_name = j.split(' ')
                full_new_name.append(split_name)
            outer_list.append(full_new_name)
        # Сортирую самый внешний список по последнему элемену самого внутреннего списка
        sorted_list = sorted(outer_list, key=lambda x: x[-1][-1])

        # Далее идет обратный процесс - процесс объединения элементов списка
        # в первоначальные имена файлов, но уже отсортированные
        new_sort = []
        for i in sorted_list:
            inner_new_sort = []
            for j in i:
                j = ' '.join(j)
                inner_new_sort.append(j)
            new_sort.append(inner_new_sort)

        last_sorted_list = []
        for i in new_sort:
            i = '/'.join(i)
            last_sorted_list.append(i)

        list_pdf_file_ticket_for_complect = last_sorted_list

        qrcode_supply_amount = supply_qrcode_to_standart_view()[0]

        while amount_of_supply_qrcode > 0:
            list_pdf_file_ticket_for_complect.append(qrcode_supply_amount)
            amount_of_supply_qrcode -= 1

        file_name = (f'web_barcode/fbs_mode/data_for_barcodes/done_data/Наклейки для комплектовщиков '
                     f'{time.strftime("%Y-%m-%d %H-%M")}.pdf')
        # print_barcode_to_pdf2(list_pdf_file_ticket_for_complect, file_name)


def clearning_folders():
    dir = 'web_barcode/fbs_mode\data_for_barcodes/'
    for file_name in os.listdir(dir):
        file_path = os.path.join(dir, file_name)
        if os.path.isfile(file_path):
            os.unlink(file_path)

    dirs = ['web_barcode/fbs_mode/data_for_barcodes/cache_dir',
            'web_barcode/fbs_mode/data_for_barcodes/done_data',
            'web_barcode/fbs_mode/data_for_barcodes/pivot_excel',
            'web_barcode/fbs_mode/data_for_barcodes/qrcode_folder/cache_dir_3',
            'web_barcode/fbs_mode/data_for_barcodes/qrcode_folder',
            'web_barcode/fbs_mode/data_for_barcodes/qrcode_supply',
            ]
    for dir in dirs:
        for filename in glob.glob(os.path.join(dir, "*")):
            file_path = os.path.join(dir, filename)
            try:
                if os.path.isfile(filename) or os.path.islink(filename):
                    os.unlink(filename)
                elif os.path.isdir(filename):
                    shutil.rmtree(filename)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (filename, e))


def create_delivery():
    """Создание поставки"""
    url_data = 'https://suppliers-api.wildberries.ru/api/v3/supplies'
    payload = json.dumps(
        {
            "name": f"Тестовая поставка {delivery_date}"
        }
    )
    # Из этой переменной достать ID поставки
    response_data = requests.request(
        "POST", url_data, headers=wb_headers_karavaev, data=payload)
    # print(response_data)
    global supply_id
    supply_id = json.loads(response_data.text)['id']


def article_data_for_tickets():
    """
    Функция обрабатывает новые сборочные задания.
    Выделяет артикулы продавца светильников, их баркоды и наименования.
    Создает словарь с данными каждого артикулы и словарь с количеством каждого
    артикула.
    """
    url = "https://suppliers-api.wildberries.ru/api/v3/orders/new"

    headers = {
        'Authorization': API_KEY_WB_IP
    }
    # Список с ID соборочных заданий
    orders_id_list = []
    # Список с артикулами_продавца соборочных заданий
    order_articles_list = []

    # Словарь с данными {id_задания: артикул_продавца}
    global article_id_dict
    article_id_dict = {}

    response = requests.request("GET", url, headers=headers)
    orders_data = json.loads(response.text)['orders']
    for order in orders_data:
        order_articles_list.append(order['article'])

    # Словарь с данными артикула: {артикул_продавца: [баркод, наименование]}
    global data_article_info_dict
    data_article_info_dict = {}
    url_data = "https://suppliers-api.wildberries.ru/content/v1/cards/cursor/list"

    # Список только для артикулов ночников. Остальные отфильтровывает
    global clear_article_list
    clear_article_list = []

    for article in order_articles_list:
        payload = json.dumps({
            "sort": {
                "cursor": {
                    "limit": 1
                },
                "filter": {
                    "textSearch": article,
                    "withPhoto": -1
                }
            }
        })
        response_data = requests.request(
            "POST", url_data, headers=wb_headers_karavaev, data=payload)
        if json.loads(response_data.text)[
                'data']['cards'][0]['object'] == "Ночники":
            clear_article_list.append(article)

            # Достаем баркод артикула (первый из списка, если их несколько)
            barcode = json.loads(response_data.text)[
                'data']['cards'][0]['sizes'][0]['skus'][0]
            # Достаем название артикула
            title = json.loads(response_data.text)[
                'data']['cards'][0]['title']
            data_article_info_dict[article] = [title, barcode]
    # Словарь с данными: {артикул_продавца: количество}
    global amount_articles
    amount_articles = dict(Counter(clear_article_list))

    for order in orders_data:
        if order['article'] in clear_article_list:
            article_id_dict[order['id']] = order['article']
            orders_id_list.append(order['id'])

    # Словарь для данных листа подбора.
    global selection_dict
    selection_dict = {}
    # Собирам данные для Листа подбора
    for order_id in article_id_dict.keys():
        payload_order = json.dumps({
            "sort": {
                "cursor": {
                    "limit": 1
                },
                "filter": {
                    "textSearch": article_id_dict[order_id],
                    "withPhoto": -1
                }
            }
        })

        response_order = requests.request(
            "POST", url_data, headers=headers, data=payload_order)
        photo = json.loads(response_order.text)[
            'data']['cards'][0]['mediaFiles'][0]
        brand = json.loads(response_order.text)[
            'data']['cards'][0]['brand']
        title_article = json.loads(response_order.text)[
            'data']['cards'][0]['title']
        print('title_article', title_article)
        seller_article = article_id_dict[order_id]
        # Заполняем словарь данными для Листа подбора
        selection_dict[order_id] = [
            photo, brand, title_article, seller_article]


def create_pivot_xls():
    '''Создает сводный файл excel с количеством каждого артикула.
    Подключается к базе данных на сервере'''
    CELL_LIMIT = 16  # ограничение символов в ячейке Excel
    COUNT_HELPER = 2
    sorted_data_for_pivot_xls = dict(
        sorted(amount_articles.items(), key=lambda v: v[0].upper()))
    pivot_xls = openpyxl.Workbook()
    create = pivot_xls.create_sheet(title='pivot_list', index=0)
    sheet = pivot_xls['pivot_list']
    sheet['A1'] = 'Артикул продавца'
    sheet['B1'] = 'Ячейка стеллажа'
    # Можно вернуть столбец для производства
    # sheet['C1'] = 'На производство'
    sheet['D1'] = 'Всего для FBS'
    sheet['E1'] = 'FBS WB'
    sheet['F1'] = 'FBS Ozon'
    # ========== РАСКРЫТЬ КОГДА ПОЯВИТСЯ ЯНДЕКС МАРКЕТ ========= #
    # sheet['G1'] = 'FBY Yandex'

    for key, value in sorted_data_for_pivot_xls.items():
        create.cell(row=COUNT_HELPER, column=1).value = key
        create.cell(row=COUNT_HELPER, column=4).value = value
        COUNT_HELPER += 1
    name_pivot_xls = 'web_barcode/fbs_mode/data_for_barcodes/pivot_excel/На производство.xlsx'
    path_file = os.path.abspath(name_pivot_xls)
    print('path', path_file)
    # file_name_dir = path.parent

    pivot_xls.save(name_pivot_xls)
    # ========= Подключение к базе данных ========= #
    engine = create_engine(
        "postgresql://databaseadmin:Up3psv8x@158.160.28.219:5432/innotreid")

    data = pd.read_sql_table(
        "database_shelvingstocks",
        con=engine,
        columns=['task_start_date',
                 'task_finish_date',
                 'seller_article_wb',
                 'seller_article',
                 'shelf_number',
                 'amount']
    )
    connection = psycopg2.connect(user="databaseadmin",
                                  # пароль, который указали при установке PostgreSQL
                                  password="Up3psv8x",
                                  host="158.160.28.219",
                                  port="5432",
                                  database="innotreid")
    cursor = connection.cursor()

    shelf_seller_article_list = data['seller_article_wb'].to_list()
    shelf_number_list = data['shelf_number'].to_list()
    shelf_amount_list = data['amount'].to_list()
    w_b = load_workbook(name_pivot_xls)
    source_page = w_b.active
    name_article = source_page['A']
    amount_all_fbs = source_page['D']

    name_article_wb = amount_articles.keys()
    for i in range(1, len(name_article)):
        # ========== РАСКРЫТЬ КОГДА ПОЯВИТСЯ ОЗОН И ЯНДЕКС МАРКЕТ ========= #
        # for j in range(len(name_article_oz)):
        #     if name_article[i].value == name_article_oz[j]:
        #         source_page.cell(row=i+1,column=6).value = amount_article_oz[j]
        # for k in range(len(name_article_ya)):
        #     if name_article[i].value == name_article_ya[k]:
        #         source_page.cell(row=i+1,column=7).value = amount_article_ya[k]

        if name_article[i].value in name_article_wb:
            source_page.cell(
                row=i+1, column=5).value = amount_articles[name_article[i].value]
        # Заполняется столбец "В" - номер ячейки на внутреннем складе
        for s in range(len(shelf_seller_article_list)):
            if name_article[i].value == shelf_seller_article_list[s] and (
                    int(amount_all_fbs[i].value) < int(shelf_amount_list[s])):
                source_page.cell(
                    row=i+1, column=2).value = shelf_number_list[s]
                new_amount = int(
                    shelf_amount_list[s]) - int(amount_all_fbs[i].value)
                select_table_query = f'''UPDATE database_shelvingstocks SET amount={new_amount},
                    task_start_date=current_timestamp, task_finish_date=NULL WHERE seller_article='{shelf_seller_article_list[s]}';'''
                cursor.execute(select_table_query)
            elif name_article[i].value == shelf_seller_article_list[s] and (
                    int(amount_all_fbs[i].value) >= int(shelf_amount_list[s])):
                # ========== Сюда вставить отметку, если мало артикулов в полке =========
                source_page.cell(
                    row=i+1, column=2).value = f'{shelf_number_list[s]}'
    connection.commit()
    w_b.save(name_pivot_xls)
    w_b2 = load_workbook(name_pivot_xls)
    source_page2 = w_b2.active
    amount_all_fbs = source_page2['D']
    amount_for_production = source_page2['C']
    PROD_DETAIL_CONST = 4
    for r in range(1, len(amount_all_fbs)):
        # Заполняет столбец ['C'] = 'Производство'
        if amount_all_fbs[r].value == 1:
            source_page2.cell(row=r+1, column=3).value = int(PROD_DETAIL_CONST)
        elif 2 <= int(amount_all_fbs[r].value) <= PROD_DETAIL_CONST-1:
            source_page2.cell(
                row=r+1, column=3).value = int(2 * PROD_DETAIL_CONST)
        elif PROD_DETAIL_CONST <= int(amount_all_fbs[r].value) <= 2 * PROD_DETAIL_CONST - 1:
            source_page2.cell(
                row=r+1, column=3).value = int(3 * PROD_DETAIL_CONST)
        else:
            source_page2.cell(row=r+1, column=3).value = ' '
    w_b2.save(name_pivot_xls)
    w_b2 = load_workbook(name_pivot_xls)
    source_page2 = w_b2.active
    amount_all_fbs = source_page2['D']
    al = Alignment(horizontal="center", vertical="center")
    al_left = Alignment(horizontal="left", vertical="center")
    # Задаем толщину и цвет обводки ячейки
    font_bold = Font(bold=True)
    thin = Side(border_style="thin", color="000000")
    thick = Side(border_style="medium", color="000000")
    for i in range(len(amount_all_fbs)):
        for c in source_page2[f'A{i+1}:G{i+1}']:
            if i == 0:
                c[0].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[1].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[2].border = Border(top=thick, left=thick,
                                     bottom=thin, right=thick)
                c[3].border = Border(top=thick, left=thick,
                                     bottom=thin, right=thick)
                c[4].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[5].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[6].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
            elif i == len(amount_all_fbs)-1:
                c[0].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[1].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[2].border = Border(top=thin, left=thick,
                                     bottom=thick, right=thick)
                c[3].border = Border(top=thin, left=thick,
                                     bottom=thick, right=thick)
                c[4].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[5].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[6].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
            else:
                c[0].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[1].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[2].border = Border(top=thin, left=thick,
                                     bottom=thin, right=thick)
                c[3].border = Border(top=thin, left=thick,
                                     bottom=thin, right=thick)
                c[4].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[5].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[6].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
            c[0].alignment = al_left
            c[1].alignment = al
            c[2].alignment = al
            c[3].alignment = al
            c[4].alignment = al
            c[5].alignment = al
            c[6].alignment = al
    source_page2.column_dimensions['A'].width = 18
    source_page2.column_dimensions['B'].width = 18
    source_page2.column_dimensions['C'].width = 18
    source_page2.column_dimensions['D'].width = 10
    source_page2.column_dimensions['E'].width = 10
    source_page2.column_dimensions['F'].width = 12
    source_page2.column_dimensions['G'].width = 12

    # Когда понадобится столбец НА ПРОИЗВОДСТВО - удалить следующую строку
    source_page2.delete_cols(3, 1)
    w_b2.save(name_pivot_xls)
    xl = DispatchEx("Excel.Application")
    xl.DisplayAlerts = False
    # print(f'{file_name_dir}/На производство.xlsx')
    folder_path = os.path.dirname(os.path.abspath(path_file))
    print('folder_path', folder_path)
    name_for_file = f'Общий файл производство ИП {delivery_date}'
    name_xls_dropbox = f'На производство ИП {delivery_date}'
    wb = xl.Workbooks.Open(path_file)
    xl.CalculateFull()
    pythoncom.PumpWaitingMessages()
    try:
        wb.ExportAsFixedFormat(
            0, f'{folder_path}/{name_for_file}.pdf')
    except Exception as e:
        print("Failed to convert in PDF format.Please confirm environment meets all the requirements  and try again")
    finally:
        wb.Close()

    # Сохраняем на DROPBOX
    with open(f'{path_file}', 'rb') as f:
        dbx_db.files_upload(
            f.read(), f'/DATABASE/beta/{name_xls_dropbox}.xlsx')
    with open(f'{folder_path}/{name_for_file}.pdf', 'rb') as f:
        dbx_db.files_upload(f.read(), f'/DATABASE/beta/{name_for_file}.pdf')


def qrcode_order():
    """
    Функция добавляет сборочные задания по их id
    в созданную поставку и получает qr стикер каждого
    задания и сохраняет его в папку
    """
    # Вызываем функцию для создания поставки и определения ее delivery_id
    for order in article_id_dict.keys():
        add_url = f'https://suppliers-api.wildberries.ru/api/v3/supplies/{supply_id}/orders/{order}'

        response = requests.request(
            "PATCH", add_url, headers=wb_headers_karavaev)

    for order in article_id_dict.keys():
        ticket_url = 'https://suppliers-api.wildberries.ru/api/v3/orders/stickers?type=png&width=58&height=40'
        payload_ticket = json.dumps({"orders": [order]})
        response_ticket = requests.request(
            "POST", ticket_url, headers=wb_headers_karavaev, data=payload_ticket)

        # Расшифровываю ответ, чтобы сохранить файл этикетки задания
        ticket_data = json.loads(response_ticket.text)["stickers"][0]["file"]

        # Узнаю стикер сборочного задания и помещаю его в словарь с данными для
        # листа подбора
        sticker_code_first_part = json.loads(response_ticket.text)[
            "stickers"][0]["partA"]
        sticker_code_second_part = json.loads(response_ticket.text)[
            "stickers"][0]["partB"]
        sticker_code = f'{sticker_code_first_part} {sticker_code_second_part}'
        selection_dict[order].append(sticker_code)

        # декодируем строку из base64 в бинарные данные
        binary_data = base64.b64decode(ticket_data)

        # создаем объект изображения из бинарных данных
        img = Image.open(BytesIO(binary_data))

        # сохраняем изображение в файл

        img.save(
            f"web_barcode/fbs_mode/data_for_barcodes/qrcode_folder/{order} {article_id_dict[order]}.png")


def create_selection_list():
    # создаем новую книгу Excel
    selection_file = Workbook()
    COUNT_HELPER = 2
    # выбираем лист Sheet1
    create = selection_file.create_sheet(title='pivot_list', index=0)
    sheet = selection_file['pivot_list']

    # Установка параметров печати
    create.page_setup.paperSize = create.PAPERSIZE_A4
    create.page_setup.orientation = create.ORIENTATION_PORTRAIT
    create.page_margins.left = 0.25
    create.page_margins.right = 0.25
    create.page_margins.top = 0.25
    create.page_margins.bottom = 0.25
    create.page_margins.header = 0.3
    create.page_margins.footer = 0.3

    sheet['A1'] = '№ Задания'
    sheet['B1'] = 'Фото'
    sheet['C1'] = 'Бренд'
    sheet['D1'] = 'Наименование'
    sheet['E1'] = 'Артикул продавца'
    sheet['F1'] = 'Стикер'

    for key, value in selection_dict.items():
        # # загружаем изображение
        response = requests.get(value[0])
        img = image.Image(io.BytesIO(response.content))
        # задаем размеры изображения
        img.width = 30
        img.height = 50

        create.cell(row=COUNT_HELPER, column=1).value = key
        # вставляем изображение в Столбец В
        sheet.add_image(img, f'B{COUNT_HELPER}')
        # create.cell(row=COUNT_HELPER, column=2).value = value[0]
        create.cell(row=COUNT_HELPER, column=3).value = value[1]
        create.cell(row=COUNT_HELPER, column=4).value = value[2]
        create.cell(row=COUNT_HELPER, column=5).value = value[3]
        create.cell(row=COUNT_HELPER, column=6).value = value[4]
        COUNT_HELPER += 1
    name_selection_file = 'web_barcode/fbs_mode/data_for_barcodes/pivot_excel/Лист подбора.xlsx'
    path_file = os.path.abspath(name_selection_file)

    selection_file.save(name_selection_file)

    w_b2 = load_workbook(name_selection_file)
    source_page2 = w_b2.active

    al = Alignment(horizontal="center", vertical="center")
    al_left = Alignment(horizontal="left", vertical="center", wrapText=True)

    source_page2.column_dimensions['A'].width = 10  # Номер задания
    source_page2.column_dimensions['B'].width = 5  # Картинка
    source_page2.column_dimensions['C'].width = 15  # Бренд
    source_page2.column_dimensions['D'].width = 25  # Наименование
    source_page2.column_dimensions['E'].width = 16  # Артикул продавца
    source_page2.column_dimensions['F'].width = 16  # Стикер

    thin = Side(border_style="thin", color="000000")
    for i in range(len(selection_dict)+1):
        for c in source_page2[f'A{i+1}:F{i+1}']:
            c[0].border = Border(top=thin, left=thin,
                                 bottom=thin, right=thin)
            c[0].font = Font(size=9)
            c[0].alignment = al

            c[1].border = Border(top=thin, left=thin,
                                 bottom=thin, right=thin)
            c[1].font = Font(size=9)
            c[1].alignment = al

            c[2].border = Border(top=thin, left=thin,
                                 bottom=thin, right=thin)
            c[2].font = Font(size=9)
            c[2].alignment = al_left

            c[3].border = Border(top=thin, left=thin,
                                 bottom=thin, right=thin)
            c[3].font = Font(size=9)
            c[3].alignment = al_left

            c[4].border = Border(top=thin, left=thin,
                                 bottom=thin, right=thin)
            c[4].font = Font(size=9)
            c[4].alignment = al_left

            c[5].border = Border(top=thin, left=thin,
                                 bottom=thin, right=thin)
            c[5].font = Font(size=9)
            c[5].alignment = al_left

    # Увеличиваем высоту строки
    for i in range(2, len(selection_dict) + 2):
        source_page2.row_dimensions[i].height = 40

    w_b2.save(name_selection_file)

    xl = DispatchEx("Excel.Application")
    xl.DisplayAlerts = False
    folder_path = os.path.dirname(os.path.abspath(path_file))
    name_for_file = f'Лист подбора {delivery_date}'
    name_xls_dropbox = f'Лист подбора {delivery_date}'
    wb = xl.Workbooks.Open(path_file)
    xl.CalculateFull()
    pythoncom.PumpWaitingMessages()
    try:
        wb.ExportAsFixedFormat(
            0, f'{folder_path}/{name_for_file}.pdf')
    except Exception as e:
        print("Failed to convert in PDF format.Please confirm environment meets all the requirements  and try again")
    finally:
        wb.Close()

    # Сохраняем на DROPBOX

    with open(f'{folder_path}/{name_for_file}.pdf', 'rb') as f:
        dbx_db.files_upload(f.read(), f'/DATABASE/beta/{name_for_file}.pdf')


def qrcode_supply():
    """
    Функция добавляет поставку в доставку, получает QR код поставки
    и преобразует этот QR код в необходимый формат.
    """
    # Переводим поставку в доставку
    url_to_supply = f'https://suppliers-api.wildberries.ru/api/v3/supplies/{supply_id}/deliver'
    response_to_supply = requests.request(
        "PATCH", url_to_supply, headers=wb_headers_karavaev)

    # Получаем QR код поставки:
    url_supply_qrcode = f"https://suppliers-api.wildberries.ru/api/v3/supplies/{supply_id}/barcode?type=png"
    response_supply_qrcode = requests.request(
        "GET", url_supply_qrcode, headers=wb_headers_karavaev)

    # Создаем QR код поставки
    qrcode_base64_data = json.loads(response_supply_qrcode.text)["file"]

    # декодируем строку из base64 в бинарные данные
    binary_data = base64.b64decode(qrcode_base64_data)
    # создаем объект изображения из бинарных данных
    img = Image.open(BytesIO(binary_data))
    # сохраняем изображение в файл
    img.save(
        f"web_barcode/fbs_mode/data_for_barcodes/qrcode_supply/{supply_id}.png")


def working_algoritm_function():
    """Функция проходит по алгоритму для создания файлов поставки"""
    clearning_folders()
    # 1. Нахожу новые сборочные задания.
    article_data_for_tickets()

    # Сохраняем все таблицы на DROPBOX
    create_pivot_xls()
    # 2. Создаю поставку
    create_delivery()

    # 3. Добавляю в созданную поставку id всех новых сборочных заданий.
    qrcode_order()

    # Создаю лист подбора
    create_selection_list()
    # 4. Добавляю поставку в доставку.
    qrcode_supply()

    if clear_article_list:
        # 5. Создаем этикетки для товаров из сборочных заданий.
        design_barcodes_dict_spec(clear_article_list, data_article_info_dict)
        # 6. Создаем список со всеми этикетками, объединяем их в один файл и сохраняем
        # в папке на Дропбокс
        list_for_print_create(amount_articles)

    # 7. Очистка всех папок от промежуточных файлов
    clearning_folders()


working_algoritm_function()
