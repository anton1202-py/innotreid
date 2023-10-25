import io
import json
import os
import time
from contextlib import closing
from datetime import date, datetime, timedelta
from time import sleep

import pandas as pd
import psycopg2
import requests
#from celery_tasks.celery import app
import telegram
from dotenv import load_dotenv
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

def add_article_price_info_to_database():
    """
    Добавляет  при вызове информацию о цене артикула на сайте
    со скидкой покупателя за текущий день.
    """

    today_data = datetime.today().strftime('%Y-%m-%d')
    ARTICLE_DATA_FILE = 'web_barcode\database\Ночники ИП.xlsx'
    path = '/DATABASE/Ночники ООО.xlsx'
    URL = 'https://card.wb.ru/cards/detail?appType=1&curr=rub&dest=-446085&regions=80,83,38,4,64,33,68,70,30,40,86,75,69,1,66,110,22,48,31,71,112,114&spp=99&nm='
    

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
        cursor.execute(
            "SELECT * FROM price_control_articlewriter")

        articles_datas = cursor.fetchall()
        
        article_dict = {}

        for i in range(len(articles_datas)):
             article_dict[articles_datas[i][2]] = articles_datas[i][1]


        data_for_database = []
        for i in article_dict.keys():

            url = URL + str(i)
            payload = {}
            headers = {}
            response = requests.request("GET", url, headers=headers, data=payload)
            data = json.loads(response.text)
            # Обход ошибки не существующиего артикула
            if data['data']['products']:
                price = int(data['data']['products'][0]['extended']['clientPriceU'])//100
                spp = data['data']['products'][0]['extended']['clientSale']
                basic_sale = data['data']['products'][0]['extended']['basicSale']
                set_with_price = (article_dict[i], i, today_data, price, spp, basic_sale)
                data_for_database.append(set_with_price)

        cursor.executemany(
                "INSERT INTO price_control_dataforanalysis (seller_article, wb_article, price_date, price, spp, basic_sale) VALUES(%s, %s, %s, %s, %s, %s);",
                data_for_database)

    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с PostgreSQL закрыто")




def change_price_info():
    """
    Возращает список сетов с информацией об артикулах с разными ценами вчера
    и сегодня. В сете данные: (артикул продавца, сегодняшняя цена, вчеращняя цена).
    """
    connection = psycopg2.connect(user=os.getenv('POSTGRES_USER'),
    # пароль, который указали при установке PostgreSQL
    password=os.getenv('POSTGRES_PASSWORD'),
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    database=os.getenv('DB_NAME'))
    cursor = connection.cursor()

    postgreSQL_select_Query = '''SELECT seller_article, price AS today_price, spp AS today_spp,
       (SELECT price FROM price_control_dataforanalysis WHERE seller_article = t.seller_article 
        AND price_date = CURRENT_DATE - INTERVAL '1 day') AS yesterday_price,
        (SELECT spp FROM price_control_dataforanalysis WHERE seller_article = t.seller_article 
        AND price_date = CURRENT_DATE - INTERVAL '1 day') AS yesterday_spp
        FROM price_control_dataforanalysis t WHERE price_date = CURRENT_DATE 
        AND price <> (SELECT price FROM price_control_dataforanalysis
        WHERE seller_article = t.seller_article AND price_date = CURRENT_DATE - INTERVAL '1 day')
        '''
    cursor.execute(postgreSQL_select_Query)

    sender_data = cursor.fetchall()
    print(sender_data)
    for article, current_price, current_spp, yesterday_price, yesterday_spp  in sender_data:
        print(f'Цена артикула {article} со скидкой покупателя {current_spp}% сегодня {current_price}, вчера была {yesterday_price} со скидкой {yesterday_spp}%')
    
    return sender_data


def sender_change_price_info():
    """
    Отправляет данные из списока сетов с информацией об артикулах
    с разными ценами вчера и сегодня.
    """
    # Получаем список всех пользователей бота
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    connection = psycopg2.connect(user=os.getenv('POSTGRES_TG_USER'),
        password=os.getenv('POSTGRES_TG_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_TG_NAME'))
    cursor = connection.cursor()

    # Подключаюсь к базе данных бота, чтобы достать всех юзеров
    tg_select_Query = '''SELECT chat_id FROM users_data;'''
    cursor.execute(tg_select_Query)    
    sender_data = cursor.fetchall()
    cursor.close()
    connection.close()
    data_for_send = change_price_info()

    # Отправка сообщения всем подписавшимся на бота
    for set_id in sender_data:
        for id in set_id:
            if len(data_for_send) > 0:
                for article, current_price, current_spp, yesterday_price, yesterday_spp  in sender_data:
                    message = f'Цена артикула {article} со скидкой покупателя {current_spp}% сегодня {current_price}, вчера была {yesterday_price} со скидкой {yesterday_spp}%'
                    bot.send_message(chat_id=id, text=message)

#add_article_price_info_to_database()
change_price_info()
