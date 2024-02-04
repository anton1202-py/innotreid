import glob
import io
import json
import os
import re
import shutil
import time
from collections import Counter
from contextlib import closing
from datetime import datetime
from pathlib import Path

import dropbox
import img2pdf
import pandas as pd
import pdfplumber
import requests
from barcode import Code128
from barcode.writer import ImageWriter
from dotenv import load_dotenv
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
from PyPDF3 import PdfFileReader, PdfFileWriter
from PyPDF3.pdf import PageObject
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

version = 'w1.0'

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


def stream_dropbox_file(path):
    _, res = dbx_db.files_download(path)
    with closing(res) as result:
        byte_data = result.content
        return io.BytesIO(byte_data)


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
    if not os.path.exists('fbs_mode/data_for_barcodes/cache_dir/'):
        os.makedirs('fbs_mode/data_for_barcodes/cache_dir/')
    with open('fbs_mode/data_for_barcodes/eac.png', 'wb') as eac_file:
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
        image1 = Image.open('fbs_mode/data_for_barcodes/eac.png')
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
        im.save(f'fbs_mode/data_for_barcodes/cache_dir/{key}.png')
        im.close()
        pdf = img2pdf.convert(
            f'fbs_mode/data_for_barcodes/cache_dir/{key}.png',
            layout_fun=layout_function)
        with open(f'fbs_mode/data_for_barcodes/cache_dir/{key}.pdf', 'wb') as f:
            f.write(pdf)


def special_design_light(dict_barcode_print):
    """
    dict_barcode_print - словарь с данными для штрихкода (артикул: [название светильника, штрихкод])
    """
    barcode_size = [img2pdf.in_to_pt(2.759), img2pdf.in_to_pt(1.95)]
    layout_function = img2pdf.get_layout_fun(barcode_size)

    font = ImageFont.truetype("arial.ttf", size=65)
    font_version = ImageFont.truetype("arial.ttf", size=35)

    current_date = datetime.now().strftime("%d.%m.%Y")
    eac_file = 'programm_data/eac light.png'

    for key, value in dict_barcode_print.items():

        render_options = {
            "module_width": 1.2,
            "module_height": 29,
            "font_size": 14,
            "text_distance": 6,
            "quiet_zone": 0
        }
        barcode = Code128(
            f'{str(value[1])[:13]}',
            writer=ImageWriter()
        ).render(render_options)
        im = Image.new('RGB', (1980, 1400), color=('#fff'))
        eac_image = Image.open(f'{eac_file}')
        cat_image = Image.open(f'programm_data/{key}.png')
        draw_text = ImageDraw.Draw(im)

        # Длина подложки
        w_width = round(im.width/2)
        # Длина штрихкода
        w = round(barcode.width/2)
        # Расположение штрихкода по центру
        position = w_width - w

        # Вставляем рисунок
        im.paste(cat_image, (1070, 120), mask=cat_image)
        # Вставляем штрихкод в основной фон
        im.paste(barcode, (position, 920))
        # Вставляем EAC в основной фон
        im.paste(eac_image, (130, 550))

        draw_text.text(
            (130, 180),
            f'{value[0]}\n',
            font=font,
            fill=('#000'), stroke_width=1
        )
        draw_text.text(
            (130, 270),
            f'Артикул: {key}\n',
            font=font,
            fill=('#000'), stroke_width=1
        )
        draw_text.text(
            (130, 360),
            f'Дата изготовления: {current_date}\n',
            font=font,
            fill=('#000'), stroke_width=1
        )
        draw_text.text(
            (1780, 70),
            version,
            font=font_version,
            fill=('#000')
        )
        im.save(f'cache_dir/{key}.png')
        im.close()
        pdf = img2pdf.convert(
            f'cache_dir/{key}.png',
            layout_fun=layout_function)
        with open(f'cache_dir/{key}.pdf', 'wb') as f:
            f.write(pdf)


def special_design_dark(dict_barcode_print):
    """
    dict_barcode_print - словарь с данными для штрихкода (артикул: [название светильника, штрихкод])
    """
    barcode_size = [img2pdf.in_to_pt(2.759), img2pdf.in_to_pt(1.95)]
    layout_function = img2pdf.get_layout_fun(barcode_size)

    font = ImageFont.truetype("arial.ttf", size=65)
    font_version = ImageFont.truetype("arial.ttf", size=35)

    current_date = datetime.now().strftime("%d.%m.%Y")
    eac_file = 'programm_data/eac dark.png'

    for key, value in dict_barcode_print.items():

        render_options = {
            "module_width": 1.13,
            "module_height": 29,
            "font_size": 14,
            "text_distance": 6,
            "quiet_zone": 4
        }
        barcode = Code128(
            f'{str(value[1])[:13]}',
            writer=ImageWriter()
        ).render(render_options)
        im = Image.new('RGB', (1980, 1400), color=('#000'))
        eac_image = Image.open(f'{eac_file}')
        cat_image = Image.open(f'programm_data/{key}.png')
        draw_text = ImageDraw.Draw(im)

        # Длина подложки
        w_width = round(im.width/2)
        # Длина штрихкода
        w = round(barcode.width/2)
        # Расположение штрихкода по центру
        position = w_width - w

        # Вставляем рисунок
        im.paste(cat_image, (1070, 120), mask=cat_image)
        # Вставляем штрихкод в основной фон
        im.paste(barcode, (position, 920))
        # Вставляем EAC в основной фон
        im.paste(eac_image, (130, 550))

        draw_text.text(
            (130, 180),
            f'{value[0]}\n',
            font=font,
            fill=('#fff'), stroke_width=1
        )
        draw_text.text(
            (130, 270),
            f'Артикул: {key}\n',
            font=font,
            fill=('#fff'), stroke_width=1
        )
        draw_text.text(
            (130, 360),
            f'Дата изготовления: {current_date}\n',
            font=font,
            fill=('#fff'), stroke_width=1
        )
        draw_text.text(
            (1780, 70),
            version,
            font=font_version,
            fill=('#ffffff')
        )
        im.save(f'cache_dir/{key}.png')
        im.close()
        pdf = img2pdf.convert(
            f'cache_dir/{key}.png',
            layout_fun=layout_function)
        with open(f'cache_dir/{key}.pdf', 'wb') as f:
            f.write(pdf)


def design_barcodes_dict_spec(names_for_print_barcodes, dict_barcode_print):
    """
    Создает дизайн штрихкода. Входящие файлы:
    names_for_print_barcodes - список всех артикулов для печати (получаем из файла).
    dict_barcode_print - словарь с информацией об артикуле: {артикул_продавца: [наименование, баркод]}
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


def print_barcode_to_pdf2(list_filenames, folder_summary_file_name, dropbox_folder):
    """
    Создает pdf файл для печати. С возможностью удаления всего кеша.
    Входящие данные:
    list_filenames - список с полными адресами и названиями файлов для объединения,
    folder_summary_file_name - полное название файла для сохранения 
    (вместе с названием папок в пути)
    dropbox_folder - папка на Дропбокс в которой будет сохранятся конечный файл
    """

    with open(list_filenames[0], "rb") as f:
        input1 = PdfFileReader(f, strict=False)
        page1 = input1.getPage(0)
        total_width = max([page1.mediaBox.upperRight[0]*(3)])
        total_height = max([page1.mediaBox.upperRight[1]*(6)])
        horiz_size = page1.mediaBox.upperRight[0]
        vertic_size = page1.mediaBox.upperRight[1]
        output = PdfFileWriter()
        file_name = folder_summary_file_name
        new_page = PageObject.createBlankPage(
            file_name, total_width, total_height)
        new_page.mergeTranslatedPage(page1, 0, vertic_size*(5))
        output.addPage(new_page)
        page_amount = (len(list_filenames) // 18)
        if len(list_filenames) % 18 > 0:
            page_amount = page_amount + 1
        pages_names = []
        for p in range(1, page_amount):
            p = PageObject.createBlankPage(
                file_name, total_width, total_height)
            output.addPage(p)
            pages_names.append(p)
        for i in range(1, len(list_filenames)):
            with open(list_filenames[i], "rb") as bb:
                # Коэффициент показывает целый остаток от деления на 18.
                m = i // 18
                # Коэффициент чтобы найти координату по вертикали
                n = (i // 3) - 6*m
                # Коэффициент чтобы найти координату по горизонтали
                # k - остаток от деления на 3
                k = i % 3
                if i < 18:
                    new_page.mergeTranslatedPage(
                        PdfFileReader(bb,
                                      strict=False).getPage(0),
                        horiz_size*(k),
                        vertic_size*(5-n))
                elif i >= 18:
                    (pages_names[m-1]).mergeTranslatedPage(
                        PdfFileReader(bb,
                                      strict=False).getPage(0),
                        horiz_size*(k),
                        vertic_size*(5-n))
                output.write(open(file_name, "wb"))
    with open(file_name, 'rb') as f:
        dbx_db.files_upload(f.read(), dropbox_folder)


def atoi(text):
    """Для сортировки файлов в списках для присоединения"""
    return int(text) if text.isdigit() else text


def natural_keys(text):
    """
    alist.sort(key=natural_keys) sorts in human order
    """
    return [atoi(c) for c in re.split(r'(\d+)', text)]


def qrcode_print_for_products():
    """
    Создает QR коды в необходимом формате и добавляет к ним артикул и его название 
    из excel файла. Сравнивает цифры из файла с QR кодами и цифры из excel файла.
    Таким образом находит артикулы и названия.
    Входящие файлы:
    filename - название файла с qr-кодами. Для создания промежуточной папки.
    """
    dir = 'fbs_mode/data_for_barcodes/qrcode_folder/'
    if not os.path.exists(dir):
        os.makedirs(dir)
    os.chmod(dir, 0o777)

    filelist = glob.glob(os.path.join(dir, "*.png"))
    filelist.sort(key=natural_keys)
    i = 0
    font1 = ImageFont.truetype("arial.ttf", size=40)
    font2 = ImageFont.truetype("arial.ttf", size=90)

    filename = 'fbs_mode/data_for_barcodes/qrcode_folder/cache_dir_3/'
    if not os.path.exists(filename):
        os.makedirs(filename)
    os.chmod(filename, 0o777)

    for file in filelist:
        path = Path(file)
        file_name = str(os.path.basename(path).split('.')[0])
        name_data = file_name.split(' ')
        sticker_data = name_data[1]
        barcode_size = [img2pdf.in_to_pt(2.759), img2pdf.in_to_pt(1.95)]
        layout_function = img2pdf.get_layout_fun(barcode_size)
        im = Image.new('RGB', (660, 466), color=('#ffffff'))
        image1 = Image.open(file)
        draw_text = ImageDraw.Draw(im)

        # Вставляем qr код в основной фон
        im.paste(image1, (40, 50))
        draw_text.text(
            (60, 25),
            f'{sticker_data}',
            font=font1,
            fill=('#000'), stroke_width=1
        )
        im.save(
            f'{filename}/{file_name}.png')
        pdf = img2pdf.convert(
            f'{filename}/{file_name}.png', layout_fun=layout_function)
        with open(f'{filename}/{file_name}.pdf', 'wb') as f:
            f.write(pdf)
        i += 1
    pdf_filenames_qrcode = glob.glob(f'{filename}/*.pdf')
    pdf_filenames_qrcode.sort(key=natural_keys)
    filelist.clear()

    # filelist = glob.glob(os.path.join(filename, "*"))
    # for f in filelist:
    #    try:
    #        os.remove(f)
    #    except Exception:
    #        print('')
    return pdf_filenames_qrcode


def supply_qrcode_to_standart_view():
    """
    Создает QR коды в необходимом формате. Входящие файлы:
    full_filename_with_qrcodes - полный путь и название до файла с qr-кодами,
    filename - название файла с qr-кодами. Для создания промежуточной папки.
    """

    dir = 'fbs_mode/data_for_barcodes/qrcode_supply/'
    filelist = glob.glob(os.path.join(dir, "*.png"))
    filelist.sort(key=natural_keys)

    for file in filelist:
        path = Path(file)
        file_name = str(os.path.basename(path).split('.')[0])
        barcode_size = [img2pdf.in_to_pt(2.759), img2pdf.in_to_pt(1.95)]
        layout_function = img2pdf.get_layout_fun(barcode_size)
        im = Image.new('RGB', (660, 466), color=('#ffffff'))
        image1 = Image.open(file)
        # Длина подложки
        w_width = round(im.width/2)
        # Высота подложки
        w_height = round(im.height/2)
        w = round(image1.width/2)
        h = round(image1.height/2)
        # Вставляем qr код в основной фон
        im.paste(image1, ((w_width - w), (w_height-h)))
        im.save(f'{dir}/{file_name}.png')
        pdf = img2pdf.convert(
            f'{dir}/{file_name}.png', layout_fun=layout_function)
        with open(f'{dir}/{file_name}.pdf', 'wb') as f:
            f.write(pdf)

    pdf_filenames_qrcode = glob.glob(f'{dir}/*.pdf')
    pdf_filenames_qrcode.sort(key=natural_keys)
    # filelist.clear()
    # dir = 'cache_dir_2/'
    # filelist = glob.glob(os.path.join(dir, "*"))
    # for f in filelist:
    #    try:
    #        os.remove(f)
    #    except Exception:
    #        print('')
    return pdf_filenames_qrcode


# def new_data_for_ozon_ticket(pdf_orders_file, csv_orders_file, out_filename):
def new_data_for_ozon_ticket(save_folder: str, fbs_ozon_common_data: dict):
    """
    Функция добавляет название артикула на этикетки с номером заказа в файле ОЗОН
    save_folder_docs - папка, где хранятся сохраненные этикетки на отправления
    fbs_ozon_common_data - словарь с данными {'номер отправления': {'артикул продавца': 'количество'}}
    """
    # Формируем список файлов во входящей папке. Названия файла - номер отправления
    list_filename = glob.glob(f'{save_folder}/*.pdf')
    # Вставляем на страницу необходимые данные
    # Регистрируем штрифт, чтобы читалась кирилица
    pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
    for file in list_filename:
        path = Path(file)
        file_name_package = os.path.basename(path).split('.')[0]
        existing_pdf = PdfFileReader(open(file, "rb"))
        output = PdfFileWriter()  # создаем новый объект PdfFileWriter
        with pdfplumber.open(file) as pdf:

            packet = io.BytesIO()
            # Создаю запись в репортлаб что вставлять и в какое место вставлять
            can = canvas.Canvas(packet, pagesize=letter)
            can.setFont('Arial', 8)
            text = ''
            text_data = fbs_ozon_common_data[file_name_package]
            for seller_article, amount in text_data.items():
                text_for_ticket = f'{seller_article} - {amount}шт'
                text += f'{text_for_ticket}\n'
            lines = text.split("\n")
            x = 11
            y = 97
            for line in lines:
                can.drawString(x, y, line)
                y -= 11  # уменьшаем координату Y для перехода на следующую строку
            can.showPage()
            can.save()
            # Move to the beginning of the StringIO buffer
            packet.seek(0)
            new_pdf = PdfFileReader(packet)
            # output = PdfFileWriter()  # перенесли создание объекта PdfFileWriter в начало цикла
            # Add the "watermark" (which is the new pdf) on the existing page
            page = existing_pdf.getPage(0)
            page.mergePage(new_pdf.getPage(0))
            # добавляем страницу в новый объект PdfFileWriter
            output.addPage(page)
        out_filename = f'{save_folder}/done/{file_name_package}.pdf'
        # Finally, write "output" to a real file
        outputStream = open(out_filename, "wb")
        output.write(outputStream)
        outputStream.close()


def new_data_for_yandex_ticket(save_folder: str, fbs_yandex_common_data: dict):
    """
    Функция добавляет название артикула на этикетки с номером заказа в файле ОЗОН
    save_folder_docs - папка, где хранятся сохраненные этикетки на отправления
    fbs_ozon_common_data - словарь с данными {'номер отправления': [{'seller_article': 'артикул', 'amount': 'количество'}]}
    """
    # Формируем список файлов во входящей папке. Названия файла - номер отправления
    list_filename = glob.glob(f'{save_folder}/*.pdf')

    # Вставляем на страницу необходимые данные
    # Регистрируем штрифт, чтобы читалась кирилица
    pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
    for file in list_filename:
        path = Path(file)
        file_name_package = os.path.basename(path).split('.')[0]
        existing_pdf = PdfFileReader(open(file, "rb"))
        output = PdfFileWriter()  # создаем новый объект PdfFileWriter

        with pdfplumber.open(file) as pdf:

            packet = io.BytesIO()
            # Создаю запись в репортлаб что вставлять и в какое место вставлять
            can = canvas.Canvas(packet, pagesize=letter)
            can.setFont('Arial', 7)
            can.rotate(90)
            text = ''
            text_data = fbs_yandex_common_data[int(file_name_package)]
            for i in text_data:
                text_for_ticket = f"{i['seller_article']} - {i['amount']}шт"
                text += f'{str(text_for_ticket)}\n'
            lines = text.split("\n")
            x = 125
            y = -330
            for line in lines:
                can.drawString(x, y, line)
                y -= 10  # уменьшаем координату Y для перехода на следующую строку
            can.showPage()
            can.save()
            # Move to the beginning of the StringIO buffer
            packet.seek(0)
            new_pdf = PdfFileReader(packet)
            # output = PdfFileWriter()  # перенесли создание объекта PdfFileWriter в начало цикла
            # Add the "watermark" (which is the new pdf) on the existing page
            page = existing_pdf.getPage(0)
            page.mergePage(new_pdf.getPage(0))
            # добавляем страницу в новый объект PdfFileWriter
            output.addPage(page)

        out_filename = f'{save_folder}/done/{file_name_package}.pdf'
        # Finally, write "output" to a real file
        outputStream = open(out_filename, "wb")
        output.write(outputStream)
        outputStream.close()


def merge_barcode_for_ozon_two_on_two(list_filenames, folder_summary_file_name):
    """
    Создает pdf файл с штрихкодами для Озона со вставкой 2х2 этикетки
    Входящие данные:
    list_filenames - список с полными адресами и названиями файлов для объединения,
    folder_summary_file_name - полное название файла для сохранения 
    (вместе с названием папок в пути)
    """
    with open(list_filenames[0], "rb") as f:
        input1 = PdfFileReader(f, strict=False)
        # Создаем новую страницу
        page1 = input1.getPage(0)
        # Задаем максимальную ширину страницы.
        # Почему-то всегда берет самую длинную сторону в качестве ширины
        total_width = max([page1.mediaBox.upperRight[0]*(2)])
        # Задаем максимальную высоту страницы.
        # Почему-то всегда берет самую короткую сторону в качестве длины
        total_height = max([page1.mediaBox.upperRight[1]*(2)])
        # Горизонтальный размер страницы
        horiz_size = page1.mediaBox.upperRight[0]
        # Вертикальный размер страницы
        vertic_size = page1.mediaBox.upperRight[1]
        # Создаем объект записи конечного файла
        output = PdfFileWriter()
        # Присваиваем имя конечного файла
        file_name = folder_summary_file_name

        # Создаем страницу конечного файла
        new_page = PageObject.createBlankPage(
            file_name, total_width, total_height)
        # Размещаем нулевой элемент на первой странице
        new_page.mergeTranslatedPage(page1, 0, vertic_size)
        # При добавлении страницы разворачиваем ее на 90 градусов.
        # Потому что длина берется всегда с длинной координаты, в у нас файл вертикальный.
        output.addPage(new_page)
        # Узнает из скольки страниц файл нам нужен
        page_amount = (len(list_filenames) // 4)
        if len(list_filenames) % 4 > 0:
            page_amount = page_amount + 1
        pages_names = []
        for p in range(1, page_amount):
            p = PageObject.createBlankPage(
                file_name, total_width, total_height)
            # При добавлении всех страниц переворачиваем их на 90 градусов, как первую.
            output.addPage(p)
            # Добавляем к новосму файлу каждую страницу в цикле
            pages_names.append(p)

        for i in range(1, len(list_filenames)):
            with open(list_filenames[i], "rb") as bb:
                # Коэффициент счетчика страниц
                m = i // 4
                # Вертикальный коэффициент. Равен либо 0, либо 1.
                if i % 4 == 0 or i % 4 == 1:
                    n = 1
                else:
                    n = 0
                # Горизонтальный коэффициент. Равен либо 0, либо 1.
                k = i % 2
                # Размещаем файлы на первой странице.
                if i < 4:
                    new_page.mergeTranslatedPage(
                        PdfFileReader(bb,
                                      strict=False).getPage(0),
                        horiz_size*(k),
                        vertic_size*(n))
                # Размещаем файлы на всех последующих страницах.
                elif i >= 4:
                    (pages_names[m-1]).mergeTranslatedPage(
                        PdfFileReader(bb,
                                      strict=False).getPage(0),
                        horiz_size*(k),
                        vertic_size*(n))
                output.write(open(file_name, "wb"))

        if len(list_filenames) == 1:
            output.write(open(file_name, "wb"))
    f.close()


def merge_barcode_for_yandex_two_on_two(list_filenames, folder_summary_file_name):
    """
    Создает pdf файл с штрихкодами для Яндекса и Озона со вставкой 2х2 этикетки
    Входящие данные:
    list_filenames - список с полными адресами и названиями файлов для объединения,
    folder_summary_file_name - полное название файла для сохранения 
    (вместе с названием папок в пути)
    """
    with open(list_filenames[0], "rb") as f:
        input1 = PdfFileReader(f, strict=False)
        # Создаем новую страницу
        page1 = input1.getPage(0)
        # Задаем максимальную ширину страницы.
        # Почему-то всегда берет самую длинную сторону в качестве ширины
        total_width = max([page1.mediaBox.upperRight[0]*(2)])
        # Задаем максимальную высоту страницы.
        # Почему-то всегда берет самую короткую сторону в качестве длины
        total_height = max([page1.mediaBox.upperRight[1]*(2)])
        # Горизонтальный размер страницы
        horiz_size = page1.mediaBox.upperRight[0]
        # Вертикальный размер страницы
        vertic_size = page1.mediaBox.upperRight[1]
        # Создаем объект записи конечного файла
        output = PdfFileWriter()
        # Присваиваем имя конечного файла
        file_name = folder_summary_file_name

        # Создаем страницу конечного файла
        new_page = PageObject.createBlankPage(
            file_name, total_width, total_height)
        # Размещаем нулевой элемент на первой странице
        new_page.mergeTranslatedPage(page1, 0, 0)
        # При добавлении страницы разворачиваем ее на 90 градусов.
        # Потому что длина берется всегда с длинной координаты, в у нас файл вертикальный.
        output.addPage(new_page.rotateClockwise(90))
        # Узнает из скольки страниц файл нам нужен
        page_amount = (len(list_filenames) // 4)
        if len(list_filenames) % 4 > 0:
            page_amount = page_amount + 1
        pages_names = []
        for p in range(1, page_amount):
            p = PageObject.createBlankPage(
                file_name, total_width, total_height)
            # При добавлении всех страниц переворачиваем их на 90 градусов, как первую.
            output.addPage(p.rotateClockwise(90))
            # Добавляем к новосму файлу каждую страницу в цикле
            pages_names.append(p)
        for i in range(1, len(list_filenames)):
            with open(list_filenames[i], "rb") as bb:
                # Коэффициент счетчика страниц
                m = i // 4
                # Вертикальный коэффициент. Равен либо 0, либо 1.
                # Совпадает с остатком от деления на 2 номера файла
                n = i % 2
                # Горизонтальный коэффициент.
                k = (i // 2) - 2 * m
                # Размещаем файлы на первой странице.
                if i < 4:
                    new_page.mergeTranslatedPage(
                        PdfFileReader(bb,
                                      strict=False).getPage(0),
                        horiz_size*(k),
                        vertic_size*(n))
                # Размещаем файлы на всех последующих страницах.
                elif i >= 4:
                    (pages_names[m-1]).mergeTranslatedPage(
                        PdfFileReader(bb,
                                      strict=False).getPage(0),
                        horiz_size*(k),
                        vertic_size*(n))
                output.write(open(file_name, "wb"))
        f.close()
