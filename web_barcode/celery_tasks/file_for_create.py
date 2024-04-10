import io
import json
import os
import time
import traceback
from contextlib import closing
from datetime import date, datetime, timedelta
from time import sleep

import dropbox
import pandas as pd
import psycopg2
import requests
import telegram
from celery_tasks.celery import app
from celery_tasks.ozon_tasks import CHAT_ID_ADMIN
from dotenv import load_dotenv
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
bot = telegram.Bot(token=TELEGRAM_TOKEN)
now_day = date.today()

tg_users_list = [269605714, 178932105]


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


def get_current_ssp():
    """
    Включается каждые 15 мин. Если СПП изменилась, то записывает данные в базу
    и отправляет сообщение в ТГ бот, что СПП поменялось
    """

    URL = 'https://card.wb.ru/cards/detail?appType=0&curr=rub&dest=-446085&regions=80,83,38,4,64,33,68,70,30,40,86,75,69,1,66,110,22,48,31,71,112,114&spp=99&nm='
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
        data_for_database = []
        if int(i) in nom_id_discount_dict:
            url = URL + str(i)
            response = requests.request("GET", url)
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
                postgreSQL_select_Query = f"""
                        SELECT spp FROM price_control_dataforanalysis WHERE id IN (
                            SELECT MAX(id) FROM price_control_dataforanalysis
                            WHERE seller_article='{article_dict[i]}' GROUP BY seller_article);
                    """
                cursor.execute(postgreSQL_select_Query)
                spp_form_db = cursor.fetchall()[0][0]
                if str(spp) != spp_form_db:
                    cursor.executemany(
                        "INSERT INTO price_control_dataforanalysis (seller_article, wb_article, price_date, price, spp, basic_sale) VALUES(%s, %s, %s, %s, %s, %s);",
                        data_for_database)
                    for set_id in tg_users_list:
                        message = f'СПП ариткула {article_dict[i]} изменилась. Была {spp_form_db}% стала {spp}%'
                        # bot.send_message(chat_id=269605714, text=message)
                        bot.send_message(
                            chat_id=set_id, text=message)
    if connection:
        cursor.close()
        connection.close()
        print("Соединение с PostgreSQL закрыто")
