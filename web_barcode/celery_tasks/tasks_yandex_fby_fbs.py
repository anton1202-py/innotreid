import json
import os
from datetime import date, datetime, timedelta

import pandas as pd
import psycopg2
import requests
import telegram
from celery_tasks.celery import app
from dotenv import load_dotenv
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

# Адрес, где лежит файл с артикулами
ARTICLE_DATA_FILE = 'web_barcode/celery_tasks/2023_08_10_yandex_sku.xlsx'
# Эндпоинт для информации по количеству товара на складе FBY
URL_FBY = f"https://api.partner.market.yandex.ru/campaigns/{os.getenv('FBY_COMPAIGNID')}/stats/skus"
# Эндпоинт для изменения остатков на складе FBS
URL_FBS = f"https://api.partner.market.yandex.ru/campaigns/{os.getenv('FBS_COMPAIGNID')}/offers/stocks"
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

headers = {
  'Content-Type': 'application/json',
  'Authorization': os.getenv('API_KEY_YANDEX')
}

#@app.task
def change_fbs_amount():
    """
    Функция смотрит остаток артикулов на складе FBY, если остаток не равен 0,
    то обнуляет остаток этого артикула на складе FBS
    """
    excel_data = pd.read_excel(ARTICLE_DATA_FILE)
    data = pd.DataFrame(excel_data, columns=['Ваш SKU'])
    article_list = data['Ваш SKU'].to_list()

    # ограничения по передачи количества артикулов в одном запросе - 500 штук. 
    residue = len(article_list) % 400 # остаток
    iter_amount = len(article_list) // 400
    # Словарь для данных по артикулу и его остатку на складе, если он != 0.
    fby_common_data_storage = {}

    for i in range(iter_amount+1):
        start_point = i*400
        finish_point = (i+1)*400
        articke_info_list = article_list[start_point:finish_point]
        # ПОСТ запрос для получения данных по артикулу
        payload = json.dumps({"shopSkus": articke_info_list})

        response = requests.request("POST", URL_FBY, headers=headers, data=payload)
        data = json.loads(response.text)
        result = data['result']
        dict_res = result['shopSkus']
        for res in dict_res:
        
            stocks_data = res['warehouses']
            stock_article = res['shopSku']

            for j in stocks_data:
                if len(j['stocks'])>0:
                    for sum in j['stocks']:
                        if sum['type'] == 'AVAILABLE':
                            fby_common_data_storage[stock_article] = sum['count']

    now = datetime.now() - timedelta(hours=3)
    time = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    for article in fby_common_data_storage.keys():
        payload = json.dumps({
          "skus": [
            {
              "sku": article,
              "warehouseId": 250643,
              "items": [
                {
                  "count": 0,
                  "type": "FIT",
                  "updatedAt": time
                }
              ]
            }
          ]
        })

        response = requests.request("PUT", URL_FBS, headers=headers, data=payload)


@app.task
def add_fby_amount_to_database():
    """
    Функция складывает остаток со склада FBY в базу данных
    раз в сутки.
    """
    add_date_stock = date.today()
    excel_data = pd.read_excel(ARTICLE_DATA_FILE)
    data = pd.DataFrame(excel_data, columns=['Ваш SKU'])
    article_list = data['Ваш SKU'].to_list()
    print(len(article_list))

    # ограничения по передачи количества артикулов в одном запросе - 500 штук.
    iter_amount = len(article_list) // 400
    # Словарь для данных по артикулу и его остатку на складе, если он != 0.
    fby_common_data_storage = {}

    for i in range(iter_amount+1):
        start_point = i*400
        if (i+1)*400 <= len(article_list):
            finish_point = (i+1)*400
        else:
            finish_point = len(article_list)
        articke_info_list = article_list[start_point:finish_point]
        # ПОСТ запрос для получения данных по артикулу
        payload = json.dumps({"shopSkus": articke_info_list})

        response = requests.request("POST", URL_FBY, headers=headers, data=payload)
        data = json.loads(response.text)
        
        result = data['result']

        dict_res = result['shopSkus']
        
        for res in dict_res:
            stocks_data = res['warehouses']
            stock_article = res['shopSku']
            stocks = stocks_data[0]
            if len(stocks['stocks']) > 0:
                for sum in stocks['stocks']:
                    #print(sum)
                    if sum['type'] == 'AVAILABLE':
                        #print(fby_common_data_storage, sum['count'])
                        fby_common_data_storage[stock_article] = sum['count']
            else:
                fby_common_data_storage[stock_article] = 0
    common_data_for_database = []
    for article, amount in fby_common_data_storage.items():
        add_data = (add_date_stock, article, 3, amount)
        common_data_for_database.append(add_data)
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
        # cursor.execute("DELETE FROM database_stocks;")
        cursor.executemany(
            "INSERT INTO database_yandex_stocks_innotreid (pub_date, article_marketplace, code_marketplace_id, amount) VALUES(%s, %s, %s, %s);",
            common_data_for_database)
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с PostgreSQL закрыто")


def sender_message():
    connection = psycopg2.connect(user=os.getenv('POSTGRES_USER'),
    # пароль, который указали при установке PostgreSQL
    password=os.getenv('POSTGRES_PASSWORD'),
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    database=os.getenv('DB_NAME'))
    cursor = connection.cursor()

    postgreSQL_select_Query = '''SELECT article_marketplace, 
           SUM(CASE WHEN date_trunc('day', pub_date) = CURRENT_DATE THEN amount ELSE 0 END) AS today_quantity,
           SUM(CASE WHEN date_trunc('day', pub_date) = date_trunc('day', CURRENT_DATE - INTERVAL '1 day') THEN amount ELSE 0 END) AS yesterday_quantity
    FROM database_yandex_stocks_innotreid
    WHERE date_trunc('day', pub_date) IN (CURRENT_DATE, date_trunc('day', CURRENT_DATE - INTERVAL '1 day'))
    GROUP BY article_marketplace
    HAVING SUM(CASE WHEN date_trunc('day', pub_date) = CURRENT_DATE THEN amount ELSE 0 END) = 0
       AND SUM(CASE WHEN date_trunc('day', pub_date) = date_trunc('day', CURRENT_DATE - INTERVAL '1 day') THEN amount ELSE 0 END) > 0;'''
    cursor.execute(postgreSQL_select_Query)

    sender_data = cursor.fetchall()

    #for article, current_amount, yesterday_amount in sender_data:
    #    print(f'Остаток на складе FBY артикула {article} сегодня {current_amount}, вчера было {yesterday_amount}')
    
    return sender_data


@app.task
def sender_zero_balance():
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
    data_for_send = sender_message()

    # Отправка сообщения всем подписавшимся на бота
    for set_id in sender_data:
        for id in set_id:
            if len(data_for_send) > 0:
                for article, current_amount, yesterday_amount in data_for_send:
                    message = f'Остаток на складе FBY артикула {article} сегодня {current_amount}, вчера было {yesterday_amount}'
                    bot.send_message(chat_id=id, text=message)
