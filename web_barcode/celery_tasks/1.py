import io
import json
import os
from contextlib import closing
from datetime import date, timedelta
from time import sleep
import time
import dropbox
import pandas as pd
import psycopg2
import requests
#from celery_tasks.celery import app
from dotenv import load_dotenv
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()
def orders_fbs_statistic():
    """Записывает в базу данных статистику по заказам со склада FBS"""
    date_from = date.today() - timedelta(3)
    date_to = date.today() - timedelta(2)

    unixtime_to = int(time.mktime(date_to.timetuple()))
    unixtime_from = int(time.mktime(date_from.timetuple()))


    url_articles = f'https://suppliers-api.wildberries.ru/content/v1/cards/cursor/list'

    APIKEY = {"Authorization": os.getenv('API_KEY_WB_USUAL')}

    response_articles = requests.get(url_articles, headers=APIKEY)
    data_articles = json.loads(response_articles.text)

    data_for_database = []

    print(len(data_articles['orders']))
    for i in data_articles['orders']:
        if i['deliveryType'] == 'fbs':
            raw_data = (date_from, i['article'], 1, i['nmId'], i['rid'])
            data_for_database.append(raw_data)

    try:
        # Подключение к существующей базе данных
        connection = psycopg2.connect(user=os.getenv('POSTGRES_USER'),
                                      dbname=os.getenv('DB_NAME'),
                                      password=os.getenv('POSTGRES_PASSWORD'),
                                      host=os.getenv('DB_HOST'),
                                      port=os.getenv('DB_PORT'))
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        # Курсор для выполнения операций с базой данных
        cursor = connection.cursor()
        # cursor.execute("DELETE FROM database_sales;")
        # cursor.execute("DELETE FROM database_stocks;")
        cursor.executemany(
            "INSERT INTO database_ordersfbsinfo (pub_date, article_marketplace, amount, nomenclature_id, rid) VALUES(%s, %s, %s, %s, %s);",
            data_for_database)
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с PostgreSQL закрыто")

orders_fbs_statistic()
