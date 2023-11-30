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


def add_article_price_info_to_database():
    """
    Добавляет при вызове информацию о цене артикула на сайте
    со скидкой покупателя за текущий день.
    """
    today_data = datetime.today().strftime('%Y-%m-%d %H:%')
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
            response = requests.request(
                "GET", url, headers=headers, data=payload)
            data = json.loads(response.text)
            # Обход ошибки не существующиего артикула
            if data['data']['products']:
                print(data)
                # Обход ошибки отсутствия spp
                if 'clientPriceU' in data['data']['products'][0]['extended'].keys():
                    price = int(data['data']['products'][0]
                                ['extended']['clientPriceU'])//100
                    spp = data['data']['products'][0]['extended']['clientSale']
                else:
                    price = int(data['data']['products'][0]
                                ['extended']['basicPriceU'])//100
                    spp = 0
                basic_sale = data['data']['products'][0]['extended']['basicSale']
                set_with_price = [article_dict[i], i,
                                  today_data, price, spp, basic_sale]
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


# def get_queryset():
#    yesterday_prices = DataForAnalysis.objects.filter(price_date=date.today()-timedelta(days=1))
#    today_prices = DataForAnalysis.objects.filter(price_date=date.today())
#    print(yesterday_prices)
#    queryset = []
#    for yesterday_price in yesterday_prices:
#        today_price = today_prices.filter(seller_article=yesterday_price.seller_article).first()
#        if today_price and today_price.price != yesterday_price.price:
#            queryset.append({
#                'seller_article': yesterday_price.seller_article,
#                'yesterday_price': yesterday_price.price,
#                'today_price': today_price.price
#            })
#    return queryset


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

    postgreSQL_select_Query = """WITH yesterday_prices AS (
        SELECT seller_article, price, spp, ROW_NUMBER() OVER(
            PARTITION BY seller_article ORDER BY id DESC) as rn
        FROM price_control_dataforanalysis
        WHERE price_date = CURRENT_DATE - INTERVAL '1 day'),
        today_prices AS (SELECT 
            seller_article, price, spp,
            ROW_NUMBER() OVER(PARTITION BY seller_article ORDER BY id DESC) as rn
            FROM price_control_dataforanalysis 
            WHERE price_date = CURRENT_DATE)
        SELECT y.seller_article, y.price as yesterday_price, y.spp as yesterday_spp,
            t.price as today_price, t.spp as today_spp
        FROM yesterday_prices y
        JOIN today_prices t ON y.seller_article = t.seller_article
        WHERE y.rn = 1 AND t.rn = 1 AND y.price != t.price;
        """
    cursor.execute(postgreSQL_select_Query)
    sender_data = cursor.fetchall()
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
    print(len(data_for_send))
    # Отправка сообщения всем подписавшимся на бота
    for set_id in sender_data:
        for id in set_id:
            if len(data_for_send) > 0:
                for article, yesterday_price, yesterday_spp, current_price, current_spp in data_for_send:
                    message = f'Цена артикула {article} со скидкой покупателя {current_spp}% сегодня {current_price}, вчера была {yesterday_price} со скидкой {yesterday_spp}%'
                    bot.send_message(chat_id=id, text=message)


def get_current_ssp():
    """
    Включается каждые 15 мин. Если СПП изменилась, то записывает данные в базу
    и отрпавляет сообщение в ТГ бот, что СПП поменялось
    """
    today_data = datetime.today().strftime('%Y-%m-%d %H:%M')
    # bot = telegram.Bot(token=TELEGRAM_TOKEN)

    URL = 'https://card.wb.ru/cards/detail?appType=2&curr=rub&dest=-446085&regions=80,83,38,4,64,33,68,70,30,40,86,75,69,1,66,110,22,48,31,71,112,114&spp=99&nm='

    try:
        # Подключение к существующей базе данных
        # connection = psycopg2.connect(user=os.getenv('POSTGRES_USER'),
        #                              dbname=os.getenv('DB_NAME'),
        #                              password=os.getenv('POSTGRES_PASSWORD'),
        #                              host=os.getenv('DB_HOST'),
        #                              port=os.getenv('DB_PORT'))
        # connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        # Курсор для выполнения операций с базой данных
        # cursor = connection.cursor()
        # cursor.execute(
        #    "SELECT * FROM price_control_articlewriter")
        #
        # articles_datas = cursor.fetchall()
        article_dict = {}
        # Подключение к базе телеграма
       # connection_tg = psycopg2.connect(user=os.getenv('POSTGRES_TG_USER'),
       #                                 password=os.getenv(
       #                                     'POSTGRES_TG_PASSWORD'),
       #                                 host=os.getenv('DB_HOST'),
       #                                 port=os.getenv('DB_PORT'),
       #                                 database=os.getenv('DB_TG_NAME'))
       # cursor_tg = connection_tg.cursor()
       # tg_select_Query = '''SELECT chat_id FROM users_data;'''
       # cursor_tg.execute(tg_select_Query)
       # sender_users = cursor_tg.fetchall()

       # for i in range(len(articles_datas)):
       #    article_dict[articles_datas[i][2]] = articles_datas[i][1]

        data_for_database = []
        # for i in article_dict.keys():

        url = URL + '64523738'
        payload = {}
        headers = {}
        response = requests.request(
            "GET", url, headers=headers, data=payload)
        data = json.loads(response.text)
        print(data['data']['products'][0]['extended'])
        # Обход ошибки не существующиего артикула
        if data['data']['products']:
            # Обход ошибки отсутствия spp
            if 'clientPriceU' in data['data']['products'][0]['extended'].keys():
                price = int(data['data']['products'][0]
                            ['extended']['clientPriceU'])//100

                spp = data['data']['products'][0]['extended']['clientSale']
            else:
                price = int(data['data']['products'][0]
                            ['extended']['basicPriceU'])//100
                spp = 0
            basic_sale = data['data']['products'][0]['extended']['basicSale']
            set_with_price = [article_dict[i], i,
                              today_data, price, spp, basic_sale]
            data_for_database.append(set_with_price)
            print(data_for_database)
            # postgreSQL_select_Query = f"""
            #    SELECT spp FROM price_control_dataforanalysis WHERE id IN (
            #        SELECT MAX(id) FROM price_control_dataforanalysis
            #        WHERE seller_article='{article_dict[i]}' GROUP BY seller_article);
            # """
            # cursor.execute(postgreSQL_select_Query)

            # spp_form_db = cursor.fetchall()[0][0]

            # if str(spp) != spp_form_db:
            #    print(article_dict[i], spp_form_db, spp)
            #    cursor.executemany(
            #        "INSERT INTO price_control_dataforanalysis (seller_article, wb_article, price_date, price, spp, basic_sale) VALUES(%s, %s, %s, %s, %s, %s);",
            #        data_for_database)
            # for set_id in sender_users:
            #   message = f'СПП ариткула {article_dict[i]} изменилась. Была {spp_form_db}% стала {spp}%'
            #   bot.send_message(chat_id=set_id[0], text=message)

    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    # finally:
    #    if connection:
    #        cursor.close()
    #        connection.close()
    #        print("Соединение с PostgreSQL закрыто")
    #    if connection_tg:
    #        cursor_tg.close()
    #        connection_tg.close()
    #        print("Соединение с PostgreSQL_TG закрыто")


# sender_change_price_info()
# get_current_ssp()

get_current_ssp()
