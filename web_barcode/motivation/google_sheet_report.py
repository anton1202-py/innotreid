import datetime
import io
import json
import os
import time
from contextlib import closing
from datetime import date, datetime, timedelta

import dropbox
import gspread
import pandas as pd
import requests
import telegram
from api_request.wb_requests import wb_article_data_from_api
from celery_tasks.celery import app
from celery_tasks.helpers_func import error_message
from django.db.models import Q, Sum
from dotenv import load_dotenv
from gspread_formatting import *
from motivation.models import Selling
from oauth2client.service_account import ServiceAccountCredentials
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg
from users.models import InnotreidUser

dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID_ADMIN = os.getenv('CHAT_ID_ADMIN')

bot = telegram.Bot(token=TELEGRAM_TOKEN)


@sender_error_to_tg
def sale_article_per_month():
    """Собирает данные по продаже артикулов за последние 30 дней"""
    # Получаем текущую дату
    current_date = datetime.today()
    current_year = current_date.year
    # Вычитаем один месяц из текущей даты
    previous_month_date = current_date - timedelta(days=current_date.day)
    previous_month_number = previous_month_date.month
    # Получаем отсортированные данные о продажах за предыдущий месяц
    sales_last_month = Selling.objects.filter(Q(month=previous_month_number), Q(lighter__designer_article=True), year=current_year) \
        .values('lighter') \
        .annotate(total_sales=Sum('quantity')) \
        .order_by('-total_sales')

    main_sales_data = []
    for data in sales_last_month:

        article_obj = Articles.objects.get(
            id=data['lighter'])
        inner_sales_article_list = ['', article_obj.common_article, article_obj.name,
                                    f'{article_obj.designer.last_name} {article_obj.designer.first_name}', data['total_sales'], datetime.now().strftime('%d-%m-%Y'), article_obj.wb_photo_address]
        main_sales_data.append(inner_sales_article_list)
    return main_sales_data


# @sender_error_to_tg
def sale_amount_per_month_for_designer():
    """Собирает сумму продаж артикулов у каждого дизайнера за предыдущий месяц"""
    # Получаем текущую дату
    current_date = datetime.today()
    current_year = current_date.year
    # Вычитаем один месяц из текущей даты
    previous_month_date = current_date - timedelta(days=current_date.day)
    previous_month_number = previous_month_date.month
    # Получаем отсортированные данные о продажах за предыдущий месяц
    sales_last_month = Selling.objects.filter(Q(month=previous_month_number), Q(lighter__designer_article=True), year=current_year) \
        .values('lighter__designer') \
        .annotate(total_sales=Sum('quantity')) \
        .order_by('-total_sales')
    print('sales_last_month', sales_last_month)

    # Составляю словарь типа {Фамилия_Имя: Количество_проданных_артикулов}
    designer_sales_info = []

    for data in sales_last_month:
        inner_dict = {}
        if InnotreidUser.objects.filter(
                id=data['lighter__designer']).exists():
            designer_obj = InnotreidUser.objects.get(
                id=data['lighter__designer'])
            print(designer_obj)
            inner_dict[f'{designer_obj.last_name} {designer_obj.first_name}'] = data['total_sales']
            designer_sales_info.append(inner_dict)
    return designer_sales_info


@sender_error_to_tg
def article_data_for_sheet():
    """Собирает данные для Google Sheet по артикулам дизайнеров"""
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


@sender_error_to_tg
def designer_google_sheet():
    """Заполняет Гугл таблицу артикулами для каждого дизайнера"""
    try:
        now_day = datetime.now().strftime('%d-%m-%Y')
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
                 "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            'celery_tasks/innotreid-a4b8ba01599c.json', scope)
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
        message_text = error_message('designer_google_sheet', designer_google_sheet, e)
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message_text, parse_mode='HTML')


@sender_error_to_tg
def article_last_month_sales_google_sheet():
    """
    Заполняет таблицу по продаже дизайнерских светильников
    за прошлый месяц. Сортирует по количеству
    """
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
                 "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            'celery_tasks/innotreid-a4b8ba01599c.json', scope)
        client = gspread.authorize(creds)
        # Open the Google Sheet using its name
        main_data = sale_article_per_month()
        sheet = client.open("Ночники дизайнеров")
        sheet_name = 'Статистика'
        statistic_sheet = sheet.worksheet(sheet_name)

        current_date = datetime.today()

        previous_month_date = current_date - timedelta(days=current_date.day)
        previous_month_number = previous_month_date.month
        previous_month_year = previous_month_date.year

        statistic_sheet.clear()
        # Добавьте названия столбцов
        statistic_sheet.update_cell(1, 1, "Фото")
        statistic_sheet.update_cell(1, 2, "Артикул")
        statistic_sheet.update_cell(1, 3, "Название")
        statistic_sheet.update_cell(1, 4, "Дизайнер")
        statistic_sheet.update_cell(
            1, 5, f"Продажи за {previous_month_number}.{previous_month_year}")
        statistic_sheet.update_cell(1, 6, "Дата обновления")

        set_row_height(
            statistic_sheet, f'2:{len(main_data)+1}', 90)
        set_column_width(statistic_sheet, 'A', 70)
        set_column_width(statistic_sheet, 'B', 100)
        set_column_width(statistic_sheet, 'C', 200)
        set_column_width(statistic_sheet, 'D', 110)
        set_column_width(statistic_sheet, 'F', 120)

        counter = 2
        for row in main_data:
            time.sleep(3)
            row_list = row
            statistic_sheet.append_row(row_list)

            time.sleep(5)
            try:
                statistic_sheet.update_cell(
                    counter, 1, f'=IMAGE(G{counter};1)')
            except:
                pass
            counter += 1

    except Exception as e:
        # обработка ошибки и отправка сообщения через бота
        message_text = error_message(
            'google_sheet', article_last_month_sales_google_sheet, e)
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message_text, parse_mode='HTML')


def common_designer_sales_last_month_google_sheet():
    """
    Заполняет таблицу по общим продажам каждого дизайнера
    за прошлый месяц
    """
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
                 "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            'celery_tasks/innotreid-a4b8ba01599c.json', scope)
        print('creds', creds)
        # client = gspread.authorize(creds)
        # # Open the Google Sheet using its name
        # main_data = sale_amount_per_month_for_designer()
        # sheet = client.open("Ночники дизайнеров")
        # sheet_name = 'Статистика'
        # statistic_sheet = sheet.worksheet(sheet_name)

        # current_date = datetime.today()

        # cells_amount = len(main_data)
        # start_cell_number = 1
        # print('Перед циклом')
        # for data in range(len(main_data)):
        #     for designer, amount in main_data[data].items():
        #         time.sleep(5)
        #     # Добавьте названия столбцов
        #         statistic_sheet.update_cell(start_cell_number+1, 9, designer)
        #         statistic_sheet.update_cell(start_cell_number+1, 10, amount)
        #         start_cell_number += 1
        # set_column_width(statistic_sheet, 'I', 150)
    except Exception as e:
        # обработка ошибки и отправка сообщения через бота
        message_text = error_message(
            'google_sheet', common_designer_sales_last_month_google_sheet, e)
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message_text, parse_mode='HTML')


@app.task
def get_data_designer_articles_to_google_sheet():
    """Записывает данные по светильникам дизайнеров и продажам в гугл таблицу"""
    designer_google_sheet()
    article_last_month_sales_google_sheet()
    common_designer_sales_last_month_google_sheet()
