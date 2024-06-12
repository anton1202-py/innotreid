import pandas as pd
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine

# Подключение к базе данных на удаленном сервере

# Чтение данных из Excel файла

connection = psycopg2.connect(user='000000000000000',
                              dbname='00000000000000',
                              password='000000000000000',
                              host='0000000000000',
                              port='000000000000000')
connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
# Курсор для выполнения операций с базой данных
cursor = connection.cursor()
sql_query = "SELECT SUM(summ) AS total_sum FROM motivation_selling WHERE year = 2023;"
# sql_query = "DELETE FROM motivation_selling WHERE year = 2023"
# # Выполняем SQL запрос с помощью курсора
cursor.execute(sql_query)


# # Подтверждаем изменения в базе данных
# connection.commit()
# Получаем результаты выборки
results = cursor.fetchall()
print(results)

# Выполняем SQL запрос с помощью курсора и передаем параметры


# df = pd.read_excel('путь_к_вашему_файлу.xlsx')
# # Загрузка данных в базу данных
# df.to_sql('название_таблицы', engine, if_exists='replace', index=False)


# excel_data_common = pd.read_excel(
#     'web_barcode/motivation/report_2024_6_6.xlsx (1).XLSX')
# column_list = excel_data_common.columns.tolist()
# excel_data = pd.DataFrame(excel_data_common, columns=[
#                           'День', 'Артикул продавца', 'Заказано, шт.', 'Сумма заказов минус комиссия WB, руб.'])
# article_list = excel_data['Артикул продавца'].to_list()
# date_list = excel_data['День'].to_list()
# orders_list = excel_data['Заказано, шт.'].to_list()
# summ_list = excel_data['Сумма заказов минус комиссия WB, руб.'].to_list()


# article_value_dict = {}
# # Список для обновления строк в БД
# new_objects = []
# marketplace_obj = 1
# ur_lico = 'ООО Иннотрейд'
# # Словарь типа {common_article: {month: {amount: quantity, price: summ}}
# year = 2023

# main_dict = {}
# for row in range(len(article_list)):
#     article = article_list[row]
#     month = date_list[row].month
#     data = date_list[row]
#     marketplace = marketplace_obj
#     quantity = orders_list[row]
#     summ = summ_list[row]
#     inner_dict = {}
#     if article not in main_dict:
#         inner_dict[month] = {'amount': quantity, 'price': summ}
#         main_dict[article] = inner_dict

#     else:
#         if month in main_dict[article]:
#             main_dict[article][month]['amount'] += quantity
#             main_dict[article][month]['price'] += summ
#         else:
#             main_dict[article][month] = {'amount': quantity, 'price': summ}
# print(len(main_dict.keys()))
# date = '2024-06-11'

# not_found = []
# # # Параметры для указания компании и общей статьи
# company_name = 'ООО Иннотрейд'
# for article, data in main_dict.items():

#     sql_query = "SELECT id FROM price_system_articles WHERE company = %s AND wb_seller_article = %s"
#     cursor.execute(sql_query, [company_name, article])
#     # # Получаем результат выполнения запроса
#     result = cursor.fetchone()

#     if result:
#         # Если запись существует, можно получить объект статьи
#         article_id = result[0]
#         for month, month_data in data.items():
#             month_summ = month_data['price']
#             month_amount = month_data['amount']

#             sql_query_sale_data = "INSERT INTO motivation_selling (lighter_id, data, marketplace_id, quantity, summ, month, year, ur_lico) VALUES(%s, %s, %s, %s, %s, %s, %s, %s);"
#             cursor.execute(sql_query_sale_data, [article_id, date, marketplace,
#                            month_amount, month_summ, month, year, company_name])
#             connection.commit()


# for article, data in main_dict.items():

#     sql_query = "SELECT id FROM price_system_articles WHERE company = %s AND wb_seller_article = %s"
#     cursor.execute(sql_query, [company_name, article])
#     # # Получаем результат выполнения запроса
#     result = cursor.fetchone()

#     if result:
#         # Если запись существует, можно получить объект статьи
#         article_id = result[0]
#     else:
#         not_found.append(article)
# print(not_found)
# print(len(not_found))

# summ_not_found = 0
# for art in not_found:
#     inner_amount = 0
#     inner_summ = 0
#     data = main_dict[art]
#     for i, j in data.items():
#         inner_amount += j['amount']
#         inner_summ += j['price']
#     print(art, f'summ: {inner_summ}, amount: {inner_amount}')
#     summ_not_found += inner_summ

# print(summ_not_found)
