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
from celery_tasks.helpers_func import error_message
from dotenv import load_dotenv
from gspread_formatting import *
from oauth2client.service_account import ServiceAccountCredentials
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg

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

bot = telegram.Bot(token=TELEGRAM_TOKEN)


@sender_error_to_tg
def article_data_for_sheet():
    """Собирает данные для Google Sheet"""

    main_data = Articles.objects.filter(
        designer_article=True
    )

    designers_data = {}

    for article in main_data:
        copy_right = 'Отрисовка'
        if article.copy_right == True:
            copy_right = 'Авторский'
        inner_dict = {'picture': article.wb_photo_address, 'common_article': article.common_article,
                      'name': article.name, 'status': copy_right}
        if article.designer not in designers_data:
            designers_data[article.designer] = [inner_dict]
        else:
            designers_data[article.designer].append(inner_dict)

    return designers_data


@app.task
def designer_google_sheet():
    """Заполняет Гугл таблицу"""
    try:
        now_day = datetime.datetime.now().strftime('%d-%m-%Y')
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
                 "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            'celery_tasks/innotreid-2c0a6335afd1.json', scope)
        client = gspread.authorize(creds)
        # Open the Google Sheet using its name
        main_data = article_data_for_sheet()
        sheet = client.open("Ночники дизайнеров")
        # sheet.clear()
        for designer, article_data_list in main_data.items():
            if designer:
                designer_name = f'{designer.last_name} {designer.first_name}'
                sheet_exists = any(
                    sheet.title == designer_name for sheet in sheet.worksheets())
                if not sheet_exists:
                    new_sheet = sheet.add_worksheet(
                        title=designer_name, rows="3000", cols="20")
                designer_sheet = sheet.worksheet(designer_name)

                designer_sheet.clear()
                # Добавьте названия столбцов
                designer_sheet.update_cell(1, 1, "Фото")
                designer_sheet.update_cell(1, 2, "Артикул")
                designer_sheet.update_cell(1, 3, "Название")
                designer_sheet.update_cell(1, 4, "Статус")
                designer_sheet.update_cell(1, 5, "Дата обновления")

                set_row_height(
                    designer_sheet, f'2:{len(article_data_list)+1}', 90)
                set_column_width(designer_sheet, 'A', 70)
                set_column_width(designer_sheet, 'B', 100)
                set_column_width(designer_sheet, 'C', 200)
                set_column_width(designer_sheet, 'D', 80)
                set_column_width(designer_sheet, 'F', 120)

                counter = 2
                for row in article_data_list:
                    time.sleep(3)
                    row_list = ['', row['common_article'],
                                row['name'], row['status'], now_day, row['picture']]
                    designer_sheet.append_row(row_list)
                    if row['status'] == 'Отрисовка':
                        fmt = CellFormat(
                            textFormat=TextFormat(
                                foregroundColor=Color(0.64, 0.64, 0.64))
                        )
                        format_cell_range(designer_sheet, f'D{counter}', fmt)
                    time.sleep(5)
                    try:
                        designer_sheet.update_cell(
                            counter, 1, f'=IMAGE(F{counter};1)')
                    except:
                        pass
                    counter += 1
    except Exception as e:
        # обработка ошибки и отправка сообщения через бота
        message_text = error_message('google_sheet', designer_google_sheet, e)
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message_text, parse_mode='HTML')
