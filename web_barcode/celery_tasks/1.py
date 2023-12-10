import io
import json
import os
import sys
import time
from contextlib import closing
from datetime import date, datetime, timedelta
from time import sleep

import dropbox
import pandas as pd
import psycopg2
import requests
import telegram
from django.conf import settings
# from celery_tasks.celery import app
from dotenv import load_dotenv
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
bot = telegram.Bot(token=TELEGRAM_TOKEN)
now_day = date.today()


def add_article_price_info_to_database():
    """
    Добавляет при вызове информацию о цене артикула на сайте
    со скидкой покупателя СПП на текущий момент. 
    Включается один раз в сутки в 9 часов утра.
    """
    try:
        URL = 'https://card.wb.ru/cards/detail?appType=0&curr=rub&dest=-446085&regions=80,83,38,4,64,33,68,70,30,40,86,75,69,1,66,110,22,48,31,71,112,114&spp=99&nm='
        # URL для определения текущей скидки, которую выставил продавец
        statistic_url = f'https://suppliers-api.wildberries.ru/public/api/v1/info?quantity=0'

        # Авторизация для получения данных от ИП Караваев
        headers_stat = {
            'Authorization': os.getenv('API_KEY_WB')
        }
        # Авторизация для получения данных от Иннотрейд
        headers_stat_innotreid = {
            'Authorization': os.getenv('API_KEY_WB_INNOTREID')
        }

        response_stat = requests.request(
            "GET", statistic_url, headers=headers_stat)
        response_stat_innotreid = requests.request(
            "GET", statistic_url, headers=headers_stat_innotreid)
        statistic_data = json.loads(response_stat.text)

        today_data = datetime.today().strftime('%Y-%m-%d %H:%M')

        # Подключение к существующей базе данных
        connection = psycopg2.connect(user=os.getenv('POSTGRES_USER'),
                                      dbname=os.getenv('DB_NAME'),
                                      password=os.getenv(
                                          'POSTGRES_PASSWORD'),
                                      host=os.getenv('DB_HOST'),
                                      port=os.getenv('DB_PORT'))
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        # Курсор для выполнения операций с базой данных
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM price_control_articlewriter")
        # Получение артикулов с базы данных сайта, по которым нужно собирать СПП
        articles_datas = cursor.fetchall()
        article_dict = {}
        for i in range(len(articles_datas)):
            article_dict[articles_datas[i][2]] = articles_datas[i][1]
        data_for_database = []
        # Словарь с ном. номером и скидкой продавца. Получаем из данных АПИ.
        nom_id_discount_dict = {}
        for statistic_wb in statistic_data:
            nom_id_discount_dict[statistic_wb['nmId']
                                 ] = [statistic_wb['price'], statistic_wb['discount']]
        # Если данные по Иннотрейд существуют, то их тоже складываем в словар.
        # Их может и не существовать, если Андрей не даст ключ
        if response_stat_innotreid:
            statistic_data_innotreid = json.loads(
                response_stat_innotreid.text)
            for statistic_wb_innotreid in statistic_data_innotreid:
                nom_id_discount_dict[statistic_wb_innotreid['nmId']
                                     ] = [statistic_wb['price'], statistic_wb['discount']]
        for i in article_dict.keys():
            url = URL + str(i)
            # Перед запуском скрипта, проверяем, что ном номер есть в словаре от АПИ.
            # Проверка нужна пока нет ключа от Иннотрейд.
            if int(i) in nom_id_discount_dict:
                response = requests.request(
                    "GET", url)
                data = json.loads(response.text)
                # Обход ошибки не существующиего артикула
                if data['data']['products']:
                    # Обход ошибки отсутствия spp
                    price = int(data['data']['products'][0]
                                ['salePriceU'])//100
                    spp = int((1 - price / (int(nom_id_discount_dict[int(i)][0]) * (
                        1 - int(nom_id_discount_dict[int(i)][1])/100))) * 100)
                    basic_sale = int(data['data']['products'][0]
                                     ['salePriceU'])//100
                    set_with_price = [article_dict[i], i,
                                      today_data, price, spp, basic_sale]
                    data_for_database.append(set_with_price)
        cursor.executemany(
            "INSERT INTO price_control_dataforanalysis (seller_article, wb_article, price_date, price, spp, basic_sale) VALUES(%s, %s, %s, %s, %s, %s);",
            data_for_database)

        if connection:
            cursor.close()
            connection.close()
            print("Соединение с PostgreSQL закрыто")
    # Если функция даст какой-то сбой, то данные об ошибке полетят в телегу.
    except Exception as er:
        message = (f'Ошибка выполнения функции add_article_price_info_to_database: <b>{er}</b>\n\n'
                   f'Что делает функция: {add_article_price_info_to_database.__doc__}')
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')


add_article_price_info_to_database()
