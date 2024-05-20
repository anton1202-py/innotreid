import asyncio

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

from .models import Articles

excel_file_address = 'price_system/Список авторских макетов общий2.xlsx'


def test_excel_file():

    order_info = pd.read_excel(excel_file_address)
    order_data = pd.DataFrame(
        order_info, columns=['Артикулы', 'Дизайнерский', 'Авторство'])

    order_article_list = order_data['Артикулы'].to_list()
    author_list = order_data['Авторство'].to_list()
    auth_dict = {}
    for i in range(len(order_article_list)):
        auth_dict[order_article_list[i]] = author_list[i]
    # print(order_number_list)
    main_articles_list = Articles.objects.all().values('common_article', 'company')
    # print(main_articles_list)
    # print(main_articles_list)
    find_articles_dict = {}
    for i in main_articles_list:
        if i['common_article']:
            for j in range(len(order_article_list)):

                if i['common_article'] in order_article_list[j]:
                    print('нашел', i['common_article'])
                    find_articles_dict[i['common_article']] = [i['company'],
                                                               True, auth_dict[order_article_list[j]]]
                    break
                else:
                    find_articles_dict[i['common_article']] = [
                        i['company'], False, False]

    # print(find_articles_dict)
    articles = []
    company_list = []
    designer_list = []
    author_list = []

    for key, value in find_articles_dict.items():
        articles.append(key)
        company_list.append(value[0])
        designer_list.append(value[1])
        author_list.append(value[2])
    data = {'Артикул': articles,
            'Компания': company_list,
            'Дизайнерский': designer_list,
            'Авторство': author_list}

    df = pd.DataFrame(data)
    # Запись данных в Excel файл
    df.to_excel('данные.xlsx', index=False)
