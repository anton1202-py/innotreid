import datetime
import json
import os
import time
from datetime import date

import gspread
import requests
import telegram
from celery_tasks.celery import app
from dotenv import load_dotenv
from gspread_formatting import *
from oauth2client.service_account import ServiceAccountCredentials

from .helpers_func import error_message

dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID_ADMIN = os.getenv('CHAT_ID_ADMIN')
bot = telegram.Bot(token=TELEGRAM_TOKEN)

API_KEY_WB = os.getenv('API_KEY_WB_IP')


def wb_data():
    """Собирает данные для Google Sheet"""
    now_day = datetime.datetime.now().strftime('%d-%m-%Y')
    try:
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
        response = requests.request("POST", url, headers=headers, data=payload)
        main_data = json.loads(response.text)['cards']
        raw_for_table_list = []
        counter = 2
        for data in main_data:
            inner_list = []
            if data['subjectName'] == 'Ночники':
                inner_list.append(data['vendorCode'])
                inner_list.append(f'=IMAGE(D{counter};1)')
                inner_list.append(data['title'])
                inner_list.append(data['photos'][0]['big'])
                inner_list.append(now_day)
                raw_for_table_list.append(inner_list)
                counter += 1

        for_table_list = sorted(raw_for_table_list, key=lambda x: x[0])

        return for_table_list
    except Exception as e:
        # обработка ошибки и отправка сообщения через бота
        message_text = error_message('wb_data', wb_data, e)
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message_text, parse_mode='HTML')


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
        print(len(data))
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
    except Exception as e:
        # обработка ошибки и отправка сообщения через бота
        message_text = error_message('google_sheet', google_sheet, e)
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message_text, parse_mode='HTML')


# google_sheet()