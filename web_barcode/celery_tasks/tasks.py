import io
import json
import os
import time
from contextlib import closing
from datetime import date, datetime, timedelta
from time import sleep

import dropbox
import pandas as pd
import psycopg2
import requests
import telegram
from celery_tasks.celery import app
from dotenv import load_dotenv
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
bot = telegram.Bot(token=TELEGRAM_TOKEN)
now_day = date.today()
tg_users_list = [178932105]


@app.task
def add_database_data():
    """
    Добавляет данные в базу взятые по API WB.
    Данные по остаткам на складах и данные продаж
    """
    control_date_stock = date.today() - timedelta(1)
    control_date_sales = date.today() - timedelta(1)

    url_stock = f"https://statistics-api.wildberries.ru/api/v1/supplier/stocks?dateFrom={control_date_stock}"
    url_sales = f"https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom={control_date_sales}&flag=1"

    # Заголовок и сам ключ
    APIKEY = {"Authorization": os.getenv('API_KEY_WB')}
    response_stock = requests.get(url_stock, headers=APIKEY)
    data_stock = json.loads(response_stock.text)
    response_sale = requests.get(url_sales, headers=APIKEY)
    data_sale = json.loads(response_sale.text)
    # Список со сводными данными для БД
    common_data_stock = []
    # Список с артикулуми с остатками со всех складов (с повторением)
    common_article_stock = []
    # Список со всеми артикулами без повторения
    new_list_stock = []
    check_data_stock = []
    for i in data_stock:
        check_data_stock.append(str(type(i)))
        if isinstance(i, dict):
            if ('diplom' not in i['supplierArticle']) and (
                    'school' not in i['supplierArticle']):
                common_article_stock.append(i['supplierArticle'])
    # Сортировка по артикулам
    common_article_stock = sorted(common_article_stock)

    for item in common_article_stock:
        if common_article_stock.count(item) >= 1 and (
                item not in new_list_stock):
            new_list_stock.append(item)

    for item in new_list_stock:
        sum_balace = 0  # Переменная для суммы остатков
        for i in data_stock:
            if item == i['supplierArticle']:
                sum_balace += int(i['quantity'])
        inner_data = (control_date_stock, item, 1, sum_balace)
        common_data_stock.append(inner_data)

    common_article_list_sale = []

    # Список для артикулов без повторения
    new_list_sale = []

    # Список сетов для загрузки в базу данных
    common_data_sale = []

    check_data_sales = []
    for i in data_sale:
        check_data_sales.append(str(type(i)))
        if isinstance(i, dict):
            if ('diplom' not in i['supplierArticle']) and (
                    'school' not in i['supplierArticle']):
                common_article_list_sale.append(i['supplierArticle'])

    common_article_list_sale = sorted(common_article_list_sale)

    for item in common_article_list_sale:
        if common_article_list_sale.count(item) >= 1 and (
                item not in new_list_sale):
            new_list_sale.append(item)

    for item in new_list_sale:
        sum = 0  # Переменная для суммы продажи
        pay = 0  # Переменная для суммы выплат
        for i in data_sale:

            if item == i['supplierArticle']:
                sum += int(i['finishedPrice'])
                pay += int(i['forPay'])
        avg_sum = sum/common_article_list_sale.count(item)
        x = (control_date_sales,
             item,
             common_article_list_sale.count(item),
             avg_sum,
             sum,
             pay,
             1)
        common_data_sale.append(x)

    if str("<class 'str'>") not in check_data_sales:
        try:
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
            # cursor.execute("DELETE FROM database_sales;")
            # cursor.execute("DELETE FROM database_stocks;")
            cursor.executemany(
                "INSERT INTO database_sales (pub_date, article_marketplace, amount, avg_price_sale, sum_sale, sum_pay, code_marketplace_id) VALUES(%s, %s, %s, %s, %s, %s, %s);",
                common_data_sale)
            cursor.executemany(
                "INSERT INTO database_stocks (pub_date, article_marketplace, code_marketplace_id, amount) VALUES(%s, %s, %s, %s);",
                common_data_stock)
        except (Exception, Error) as error:
            print("Ошибка при работе с PostgreSQL", error)
        finally:
            if connection:
                cursor.close()
                connection.close()
    else:
        sleep(10)


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


def wb_articles_list(header, offset=0, article_price_data=None, iter_numb=0):
    """Получаем массив арткулов с ценами и скидками для ВБ"""
    if article_price_data == None:
        article_price_data = []
    url = f'https://discounts-prices-api.wb.ru/api/v2/list/goods/filter?limit=1000&offset={offset}'

    response = requests.request("GET", url, headers=header)
    if response.status_code == 200:
        main_data = json.loads(response.text)['data']['listGoods']
        for data in main_data:
            inner_dict = {}
            inner_dict['nmId'] = data['nmID']
            inner_dict['price'] = data['sizes'][0]['price']
            inner_dict['discount'] = data['discount']
            article_price_data.append(inner_dict)
        if len(main_data) == 1000:
            iter_numb += 1
            offset = 1000 * iter_numb
            wb_articles_list(header, offset, article_price_data, iter_numb)
        return article_price_data
    else:
        time.sleep(10)
        return wb_articles_list(header, offset, article_price_data, iter_numb)


@app.task
def add_article_price_info_to_database():
    """
    Добавляет при вызове информацию о цене артикула на сайте
    со скидкой покупателя СПП на текущий момент. 
    Включается один раз в сутки в 12 часов.
    """
    try:
        URL = 'https://card.wb.ru/cards/detail?appType=0&curr=rub&dest=-446085&regions=80,83,38,4,64,33,68,70,30,40,86,75,69,1,66,110,22,48,31,71,112,114&spp=99&nm='
        # URL для определения текущей скидки, которую выставил продавец

        # Авторизация для получения данных от ИП Караваев
        headers_stat = {
            'Authorization': os.getenv('API_KEY_WB')
        }
        # Авторизация для получения данных от Иннотрейд
        headers_stat_innotreid = {
            'Authorization': os.getenv('API_KEY_WB_INNOTREID')
        }

        response_stat_ip = wb_articles_list(headers_stat)
        response_stat_innotreid = wb_articles_list(headers_stat_innotreid)
        statistic_data = response_stat_ip

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
            statistic_data_innotreid = response_stat_innotreid
            for statistic_wb_innotreid in statistic_data_innotreid:
                nom_id_discount_dict[statistic_wb_innotreid['nmId']
                                     ] = [statistic_wb_innotreid['price'], statistic_wb_innotreid['discount']]
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
    # Если функция даст какой-то сбой, то данные об ошибке полетят в телегу.
    except Exception as er:
        message = (f'Ошибка выполнения функции add_article_price_info_to_database: <b>{er}</b>\n\n'
                   f'Что делает функция: {add_article_price_info_to_database.__doc__}')
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')


def add_one_article_info_to_db(seller_article, wb_article):
    """
    Добавляет при вызове информацию о цене одного артикула на сайте
    со скидкой покупателя за текущий момент.
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
                                      password=os.getenv('POSTGRES_PASSWORD'),
                                      host=os.getenv('DB_HOST'),
                                      port=os.getenv('DB_PORT'))
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        # Курсор для выполнения операций с базой данных
        cursor = connection.cursor()
        data_for_database = []
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
                                     ] = [statistic_wb_innotreid['price'], statistic_wb_innotreid['discount']]

        if str(wb_article) in nom_id_discount_dict:
            url = URL + str(wb_article)
            response = requests.request("GET", url)
            data = json.loads(response.text)
            # Обход ошибки не существующиего артикула
            if data['data']['products']:
                # Обход ошибки отсутствия spp
                price = int(data['data']['products'][0]
                            ['salePriceU'])//100
                spp = int((1 - price / (int(nom_id_discount_dict[int(wb_article)][0]) / (
                    1 - int(nom_id_discount_dict[int(wb_article)][1])/100))) * 100)
                basic_sale = int(data['data']['products'][0]
                                 ['salePriceU'])//100
                set_with_price = [seller_article, wb_article,
                                  today_data, price, spp, basic_sale]
                data_for_database.append(set_with_price)
        cursor.executemany(
            "INSERT INTO price_control_dataforanalysis (seller_article, wb_article, price_date, price, spp, basic_sale) VALUES(%s, %s, %s, %s, %s, %s);",
            data_for_database)

        if connection:
            cursor.close()
            connection.close()
    except Exception as er:
        message = (f'Ошибка выполнения функции add_one_article_info_to_db: <b>{er}</b>\n\n'
                   f'Что делает функция: {add_one_article_info_to_db.__doc__}')
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
