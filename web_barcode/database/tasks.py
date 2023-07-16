from datetime import date,  timedelta
import json
import requests


def database_add_data():
    control_date_stock = date.today() - timedelta(days=1)
    control_date_sales = date.today() - timedelta(days=1)

    url_stock = f"https://statistics-api.wildberries.ru/api/v1/supplier/stocks?dateFrom={control_date_stock}"
    url_sales = f"https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom={control_date_sales}&flag=1"

    # Заголовок и сам ключ
    APIKEY = {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NJRCI6Ijk0NTkwZjcwLTAxNzEtNGI5YS05ZjU0LTc4MDVkNDJjZjRiNiJ9.es_8LgoQ1WOKAjmx6NSV6y2Ue2rUnrEVPdlwbz96GwI"}
    response_stock = requests.get(url_stock, headers=APIKEY)
    data_stock = json.loads(response_stock.text) 
    print(data_stock)

    """
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
            if ('diplom' not in i['supplierArticle']) and ('school' not in i['supplierArticle']):
                common_article_stock.append(i['supplierArticle'])
    # Сортировка по артикулам
    common_article_stock = sorted(common_article_stock)

    for item in common_article_stock:
        if common_article_stock.count(item) >= 1 and item not in new_list_stock:
            new_list_stock.append(item)

    for item in new_list_stock:
        sum_balace = 0 # Переменная для суммы остатков
        for i in data_stock:
            if item == i['supplierArticle']:
                sum_balace += int(i['quantity'])
        inner_data = (control_date_stock, item, 1, sum_balace)
        common_data_stock.append(inner_data)

    try:
        # Подключение к существующей базе данныx
        connection = psycopg2.connect(user="databaseadmin",
                                      dbname="innotrade",
                                      # пароль, который указали при установке PostgreSQL
                                      password="Up3psv8x",
                                      host="127.0.0.1",
                                      port="5432")
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        # Курсор для выполнения операций с базой данных
        cursor = connection.cursor()
        cursor.executemany("INSERT INTO database_stocks (pub_date, article_marketplace, code_marketplace_id, amount) VALUES(%s, %s, %s, %s);", common_data_stock)
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с PostgreSQL закрыто")
    
    
    common_article_list_sale = []

    # Список для артикулов без повторения
    new_list_sale = []

    # Список сетов для загрузки в базу данных
    common_data_sale = []

    for i in data_sale:
        if ('diplom' not in i['supplierArticle']) and ('school' not in i['supplierArticle']):
            common_article_list_sale.append(i['supplierArticle'])

    common_article_list_sale = sorted(common_article_list_sale)

    for item in common_article_list_sale:
        if common_article_list_sale.count(item) >= 1 and item not in new_list_sale:
            new_list_sale.append(item)

    for item in new_list_sale:
        sum = 0 # Переменная для суммы продажи
        pay = 0 # Переменная для суммы выплат
        for i in data_sale:

            if item == i['supplierArticle']:
                sum += int(i['finishedPrice'])
                pay += int(i['forPay'])
        avg_sum = sum/common_article_list_sale.count(item)
        x = (control_date_sales, item, common_article_list_sale.count(item), avg_sum, sum, pay, 1)
        common_data_sale.append(x)
    print(common_data_stock)
    if (str("<class 'str'>") not in check_data_sales) and (str("<class 'str'>") not in check_data_stock):
        print('УРА!!!')
        try:
            # Подключение к существующей базе данных
            connection = psycopg2.connect(user="postgres",
                                          dbname="Innotrade",
                                          password="1",
                                          host="localhost",
                                          port="5432")
            connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            # Курсор для выполнения операций с базой данных
            cursor = connection.cursor()
            #cursor.execute("DELETE FROM database_sales;")
            #cursor.execute("DELETE FROM database_stocks;")
            #cursor.executemany("INSERT INTO database_stocks (pub_date, article_marketplace, code_marketplace_id, amount) VALUES(%s, %s, %s, %s);", common_data_stock)
            #cursor.executemany("INSERT INTO database_sales (pub_date, article_marketplace, amount, avg_price_sale, sum_sale, sum_pay, code_marketplace_id) VALUES(%s, %s, %s, %s, %s, %s, %s);", common_data_sale)

        except (Exception, Error) as error:
            print("Ошибка при работе с PostgreSQL", error)
        finally:
            if connection:
                cursor.close()
                connection.close()
                print("Соединение с PostgreSQL закрыто")"""
    #else:
    #    print('АХТУНГ!!!')
    #    sleep(10)
    #    database_add_data()


database_add_data()
