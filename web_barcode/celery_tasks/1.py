import io
import json
import os
import sys
import time
from contextlib import closing
from datetime import date, datetime, timedelta
from time import sleep

import dropbox
import gspread
import pandas as pd
import psycopg2
import requests
import telegram
from django.conf import settings
# from celery_tasks.celery import app
from dotenv import load_dotenv
from gspread_formatting import *
from helpers_func import error_message
from oauth2client.service_account import ServiceAccountCredentials
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)

REFRESH_TOKEN_DB = os.getenv('REFRESH_TOKEN_DB')
APP_KEY_DB = os.getenv('APP_KEY_DB')
APP_SECRET_DB = os.getenv('APP_SECRET_DB')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID_ADMIN = os.getenv('CHAT_ID_ADMIN')
bot = telegram.Bot(token=TELEGRAM_TOKEN)

API_KEY_WB = os.getenv('API_KEY_WB_IP')

dbx_db = dropbox.Dropbox(oauth2_refresh_token=REFRESH_TOKEN_DB,
                         app_key=APP_KEY_DB,
                         app_secret=APP_SECRET_DB)


def stream_dropbox_file(path):
    _, res = dbx_db.files_download(path)
    with closing(res) as result:
        byte_data = result.content
        return io.BytesIO(byte_data)


def wb_data():
    url = 'https://suppliers-api.wildberries.ru/content/v2/get/cards/list'
    payload = json.dumps({
        "settings": {
            "cursor": {
                "limit": 1000
            },
            "filter": {
                "withPhoto": -1
            }
        }
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': API_KEY_WB
    }

    MATCHING_LIST = '/DATABASE/список сопоставления.xlsx'
    matching_list_data = stream_dropbox_file(MATCHING_LIST)

    df = pd.read_excel(matching_list_data)

    special_tickets_data_file = pd.DataFrame(
        df, columns=['Артикул'])

    new_list = special_tickets_data_file['Артикул'].to_list()
    # print(new_list)

    response = requests.request("POST", url, headers=headers, data=payload)
    main_data = json.loads(response.text)['cards']
    for_table_list = []
    counter = 2
    for data in main_data:
        inner_list = []
        if data['subjectName'] == 'Ночники':
            if data['vendorCode'] not in new_list:
                inner_list.append(data['vendorCode'])
                inner_list.append(f'=IMAGE(D{counter};1)')
                inner_list.append(data['title'])
                inner_list.append(data['photos'][0]['big'])
                for_table_list.append(inner_list)
                counter += 1
    return for_table_list


def google_sheet():
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

    data = wb_data()

    set_row_height(sheet, f'2:{len(data)}', 175)
    set_column_width(sheet, 'A', 100)
    set_column_width(sheet, 'B', 130)
    set_column_width(sheet, 'C', 400)
    set_column_width(sheet, 'D', 300)

    counter = 2
    for row in data:
        time.sleep(1)
        sheet.append_row(row)
        time.sleep(3)
        try:
            sheet.update_cell(
                counter, 2, f'=IMAGE(D{counter};1)')
        except:
            pass
        counter += 1


wb_data()
# google_sheet()
