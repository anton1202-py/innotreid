import io
import json
import os
from contextlib import closing
from datetime import date, timedelta
import time
from time import sleep

import dropbox
import pandas as pd
import psycopg2
import requests
from celery_tasks.celery import app
from dotenv import load_dotenv
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

@app.task
def add_database_data():
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
        print('УРА!!!')
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
                print("Соединение с PostgreSQL закрыто")
    else:
        sleep(10)


@app.task
def orders_fbs_statistic():
    """Записывает в базу данных статистику по заказам со склада FBS"""
    date_from = date.today() - timedelta(3)
    date_to = date.today() - timedelta(2)

    unixtime_to = int(time.mktime(date_to.timetuple()))
    unixtime_from = int(time.mktime(date_from.timetuple()))

    url_articles = f'https://suppliers-api.wildberries.ru/api/v3/orders?limit=1000&next=0&dateFrom={unixtime_from}&dateTo={unixtime_to}&flag=1'

    APIKEY = {"Authorization": os.getenv('API_KEY_WB_USUAL')}

    response_articles = requests.get(url_articles, headers=APIKEY)
    data_articles = json.loads(response_articles.text)

    data_for_fbs_database = []

    for i in data_articles['orders']:
        if i['deliveryType'] == 'fbs':
            raw_data = (date_from, i['article'], 1, i['nmId'], i['rid'])
            data_for_fbs_database.append(raw_data)

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
            data_for_fbs_database)
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с PostgreSQL закрыто")


@app.task
def add_stock_data_from_frontend():
    refresh_token_db = os.getenv('REFRESH_TOKEN_DB')
    app_key_db = os.getenv('APP_KEY_DB')
    app_secret_db = os.getenv('APP_SECRET_DB')
    dbx_db = dropbox.Dropbox(oauth2_refresh_token=refresh_token_db,
                          app_key=app_key_db,
                          app_secret=app_secret_db)
    date_stock = date.today()

    wb_stock_id_name = {
        507: 'Коледино', 686: 'Новосибирск', 1193: 'Хабаровск', 1733: 'Екатеринбург',
        2737: 'Санкт-Петербург', 115651: 'FBS Тамбов', 117392: 'FBS Владимир',
        117414:	'FBS Уткина Заводь', 117419: 'FBS Новосибирск', 117442: 'Калуга',
        117501:	'Подольск', 117866:	'Тамбов', 117986: 'Казань', 118365:	'FBS Красноярск',
        119261:	'FBS Коледино', 120762: 'Электросталь', 121700: 'FBS Минск',
        121709:	'Электросталь', 122252:	'FBS Москва 72', 122259: 'FBS Москва',
        122495:	'FBS Астана', 130744: 'Краснодар ', 131643: 'FBS Иркутск',
        132043:	'FBS Санкт-Петербург', 133533: 'FBS Ростов-на-Дону', 144046: 'FBS Калуга',
        144154:	'FBS Симферополь', 146666: 'FBS Самара', 146725: 'FBS Тюмень',
        152588:	'FBS Волгоград', 152594: 'FBS Рязань', 152610: 'FBS Тверь', 152611: 'FBS Челябинск',
        152612:	'FBS Ярославль', 152700: 'FBS Уфа', 157848:	'FBS Пенза', 158448: 'FBS Ставрополь',
        158929:	'FBS Саратов', 159402: 'Шушары ', 161812: 'Санкт-Петербург', 168826: 'FBS Лобня',
        172073:	'FBS Ижевск', 172075: 'FBS Курск', 172430:	'Барнаул', 204212:	'FBS Солнцево',
        204492:	'FBS Астрахань', 204493: 'FBS Барнаул', 204494: 'FBS Брянск', 204495: 'FBS Владикавказ',
        204496:	'FBS Вологда', 204497: 'FBS Пятигорск', 204498: 'FBS Серов', 204499: 'FBS Чебоксары',
        204615:	'Томск',
        204939:	'Астана',
        205104:	'Ульяновск',
        205205:	'Киров',
        205228:	'Белая Дача',
        206236:	'Белые Столбы',
        206239:	'FBS Белая Дача',
        206348:	'Алексин',
        206708:	'Новокузнецк',
        206844:	'Калининград',
        206968:	'Чехов',
        207743:	'Пушкино',
        208277:	'Невинномысск',
        208761:	'FBS Калининград',
        208768:	'FBS Абакан',
        208771:	'FBS Гомель',
        208772:	'FBS Иваново',
        208773:	'FBS Киров',
        208774:	'FBS Крыловская',
        208776:	'FBS Липецк',
        208777:	'FBS Мурманск',
        208778:	'FBS Набережные Челны',
        208780:	'FBS Оренбург',
        208781:	'FBS Печатники',
        208782:	'FBS Пушкино',
        208783:	'FBS Смоленск',
        208784:	'FBS Сургут',
        208785:	'FBS Темрюк',
        208786:	'FBS Томск',
        208787:	'FBS Чита',
        208789:	'FBS Новокузнецк',
        208815:	'FBS Екатеринбург',
        208816:	'FBS Ереван',
        208817:	'FBS Казань',
        208818:	'FBS Краснодар',
        208819:	'FBS Шушары',
        208820:	'FBS Хабаровск',
        208941:	'Домодедово',
        209106:	'FBS Чертановский',
        209107:	'FBS Нахабино',
        209108:	'FBS Курьяновская',
        209109:	'FBS Комсомольский',
        209110:	'FBS Южные ворота',
        209111:	'FBS Гольяново',
        209112:	'FBS Белые Столбы',
        209113:	'FBS Черная грязь',
        209510:	'FBS Электросталь',
        209513:	'Домодедово',
        209591:	'FBS Омск',
        209592:	'FBS Пермь',
        209601:	'FBS Невинномысск',
        209649:	'FBS Алексин',
        209902:	'FBS Артём',
        209950:	'FBS Ульяновск',
        210001:	'Чехов 2',
        210515:	'Вёшки',
        210815:	'FBS Хоргос',
        210967:	'FBS Домодедово',
        211622:	'Минск',
        211672:	'FBS Минск 2',
        211730:	'FBS Внуково',
        211790:	'FBS Екатеринбург 2',
        211895:	'FBS Воронеж',
        212031:	'FBS Мытищи',
        212032:	'FBS Вешки',
        212038:	'FBS Алматы 2',
        212419:	'FBS Нижний Новгород',
        213651:	'FBS Нижний Тагил',
        213892:	'FBS Белгород',
        214110:	'FBS Архангельск',
        214111:	'FBS Псков',
        214112:	'FBS Белогорск',
        215049:	'FBS Махачкала',
        216462:	'FBS Кемерово',
        216745:	'FBS Бишкек',
        217390:	'FBS Байсерке',
        217650:	'FBS Санкт-Петербург WBGo',
        217678:	'Внуково',
        217906:	'FBS Москва WBGo 2',
        218110:	'FBS Москва WBGo',
        218119:	'FBS Астана',
        218210:	'Обухово',
        218268:	'FBS Москва WBGo 3',
        218402:	'Иваново',
        218579:	'FBS Москва WBGo 4',
        218623:	'Подольск 3',
        218637:	'FBS Ташкент',
        218654:	'FBS Чехов',
        218658:	'FBS Москва WBGo 5',
        218659:	'FBS Москва WBGo 6',
        218660:	'FBS Москва WBGo 7',
        218671:	'FBS Обухово',
        218672:	'FBS Москва WBGo 8',
        218675:	'FBS Иваново',
        218699:	'FBS Шымкент',
        218720:	'FBS Ростов-на-Дону',
        218733:	'FBS Ош',
        218804:	'FBS Белая Дача',
        218841:	'FBS Ижевск',
        218893:	'FBS Южно-Сахалинск',
        218894:	'FBS Якутск',
        218904:	'FBS Москва WBGo 9',
        218905:	'FBS Москва WBGo 10',
        218906:	'FBS Москва WBGo 11',
        218907:	'FBS Москва WBGo 12',
        218951:	'FBS Москва WBGo 13',
        218952:	'FBS Москва WBGo 14',
        218953:	'FBS Москва WBGo 15',
        218991:	'FBS Чехов 2',
        100001056: 'СЦ Тест',
        100001346: 'СЦ для вычитания Нур-Султан',
        100002577: 'СЦ для вычитания восточный КЗ',
        100002632: 'FBS для отключения тест',
        100002632: 'FBS для отключения тест',
    }


    ARTICLE_DATA_FILE = 'web_barcode\database\Ночники ИП.xlsx'
    path = '/DATABASE/Ночники ИП.xlsx'
    URL = 'https://card.wb.ru/cards/detail?regions=80,64,83,4,38,33,70,68,69,86,30,40,48,1,22,66,31&dest=-2133464&nm='
    def stream_dropbox_file(path):
            _,res=dbx_db.files_download(path)
            with closing(res) as result:
                byte_data=result.content
                return io.BytesIO(byte_data)

    main_file = stream_dropbox_file(path)
    excel_data = pd.read_excel(main_file)
    data_3 = pd.DataFrame(excel_data, columns = ['Артикул продавца',
                                                       'Номенклатура'])
    nomenclatura_list_int = data_3['Номенклатура'].to_list()
    article_list = data_3['Артикул продавца'].to_list()

    article_dict = {}

    for i in range(len(nomenclatura_list_int)):
         article_dict[nomenclatura_list_int[i]] = article_list[i]

    iter_amount = len(article_dict.keys()) // 15

    data_for_database = []
    for k in range(iter_amount+1):
        start_point = k*15
        finish_point = (k+1)*15
        nom_info_list = list(article_dict.keys())[start_point:finish_point]

        helper = ''
        for i in nom_info_list:
            helper += str(i)+';'
        url = URL + str(helper)
        payload = {}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)

        data = json.loads(response.text)
        main_data = data['data']['products']

        for j in main_data:
            amount = 0
            art = article_dict[j['id']]

            for i in j['sizes'][0]['stocks']:           
                if  'FBS' not in wb_stock_id_name[i['wh']]:
                    amount += i["qty"]
                    inner_data_set = (date_stock, art, j['id'], wb_stock_id_name[i['wh']], i["qty"])
                    data_for_database.append(inner_data_set)

            raw_data_for_database = (date_stock, art, j['id'], 'Итого по складам', amount)
            data_for_database.append(raw_data_for_database)
            sleep(1)
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
            "INSERT INTO database_stocks_wb_frontend (pub_date, seller_article_wb, article_wb, stock_name, amount) VALUES(%s, %s, %s, %s, %s);",
            data_for_database)
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с PostgreSQL закрыто")
