import datetime
import io
import json
import os
import time
from contextlib import closing
from datetime import date

import dropbox
import gspread
import pandas as pd
import requests
import telegram
from api_request.wb_requests import wb_article_data_from_api
from celery_tasks.celery import app
from dotenv import load_dotenv
from gspread_formatting import *
from oauth2client.service_account import ServiceAccountCredentials
from price_system.supplyment import sender_error_to_tg

from .helpers_func import error_message

dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID_ADMIN = os.getenv('CHAT_ID_ADMIN')
REFRESH_TOKEN_DB = os.getenv('REFRESH_TOKEN_DB')
APP_KEY_DB = os.getenv('APP_KEY_DB')
APP_SECRET_DB = os.getenv('APP_SECRET_DB')
API_KEY_WB = os.getenv('API_KEY_WB_IP')
MATCHING_DB_FILE = '/DATABASE/список сопоставления.xlsx'

dbx_db = dropbox.Dropbox(oauth2_refresh_token=REFRESH_TOKEN_DB,
                         app_key=APP_KEY_DB,
                         app_secret=APP_SECRET_DB)

bot = telegram.Bot(token=TELEGRAM_TOKEN)


@sender_error_to_tg
def stream_dropbox_file(path):
    _, res = dbx_db.files_download(path)
    with closing(res) as result:
        byte_data = result.content
        return io.BytesIO(byte_data)


@sender_error_to_tg
def dropbox_matching_data():
    """Возвращает список устаревших артикулов ВБ для сравнения"""
    matching_file = stream_dropbox_file(MATCHING_DB_FILE)
    matching_file_read = pd.read_excel(matching_file)
    matching_file_read_data = pd.DataFrame(
        matching_file_read, columns=['Артикул'])
    matching_list = matching_file_read_data['Артикул'].to_list()
    return matching_list


@sender_error_to_tg
def wb_data():
    """Собирает данные для Google Sheet"""
    now_day = datetime.datetime.now().strftime('%d-%m-%Y')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': API_KEY_WB
    }

    main_data = wb_article_data_from_api(headers)
    raw_for_table_list = []
    counter = 2
    matching_list = dropbox_matching_data()
    for data in main_data:
        inner_list = []
        if data['subjectName'] == 'Ночники':
            if data['vendorCode'] not in matching_list and 'photos' in data.keys():
                inner_list.append(data['vendorCode'])
                inner_list.append(f'=IMAGE(D{counter};1)')
                inner_list.append(data['title'])
                inner_list.append(data['photos'][0]['big'])
                inner_list.append(now_day)
                raw_for_table_list.append(inner_list)
                counter += 1
    for_table_list = sorted(raw_for_table_list, key=lambda x: x[0])
    return for_table_list


@app.task
def google_sheet():
    """Заполняет Гугл таблицу"""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
                 "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            'celery_tasks/innotreid-2c0a6335afd1.json', scope)
        client = gspread.authorize(creds)

        # Open the Google Sheet using its name
        sheet = client.open("3D Ночник").sheet1
        sheet.clear()
        # Добавьте названия столбцов
        sheet.update_cell(1, 1, "Артикул")
        sheet.update_cell(1, 2, "Фото")
        sheet.update_cell(1, 3, "Наименование")
        sheet.update_cell(1, 4, "медиафайлы")
        sheet.update_cell(1, 5, "Дата обновления")

        data = wb_data()

        set_row_height(sheet, f'2:{len(data)+1}', 175)
        set_column_width(sheet, 'A', 100)
        set_column_width(sheet, 'B', 130)
        set_column_width(sheet, 'C', 400)
        set_column_width(sheet, 'D', 300)

        counter = 2
        for row in data:
            time.sleep(3)
            sheet.append_row(row)
            time.sleep(5)
            try:
                sheet.update_cell(
                    counter, 2, f'=IMAGE(D{counter};1)')
            except:
                pass
            counter += 1
    except Exception as e:
        # обработка ошибки и отправка сообщения через бота
        message_text = error_message('google_sheet', google_sheet, e)
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message_text, parse_mode='HTML')
        google_sheet()
