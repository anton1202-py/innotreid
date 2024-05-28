import json
import math
import os
import time
from datetime import datetime, timedelta

import pandas as pd
import requests
import telegram
from database.models import CodingMarketplaces, OzonSales, WildberriesSales
from django.http import HttpResponse
# from celery_tasks.celery import app
from dotenv import load_dotenv
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, PatternFill, Side
from price_system.models import Articles, DesignUser
from price_system.supplyment import sender_error_to_tg
from reklama.models import (AdvertisingCampaign, CompanyStatistic,
                            DataOooWbArticle, OooWbArticle, OzonCampaign,
                            ProcentForAd, SalesArticleStatistic,
                            WbArticleCommon, WbArticleCompany)

from web_barcode.constants_file import (CHAT_ID_ADMIN, TELEGRAM_TOKEN,
                                        header_ozon_dict, header_wb_data_dict,
                                        header_wb_dict, header_yandex_dict,
                                        ozon_adv_client_access_id_dict,
                                        ozon_adv_client_secret_dict,
                                        ozon_api_token_dict,
                                        wb_headers_karavaev, wb_headers_ooo,
                                        yandex_business_id_dict)

from .models import Selling


def articles_data_merge():
    main_data = Articles.objects.all()
    print(len(main_data))


def get_current_selling():
    """Получаем текущие продажи артикулов"""
    # ozon_sale_data = OzonSales.objects.all()
    article_data = Articles.objects.all()
    date = datetime.now()
    january = date - timedelta(days=20)
    january_month = int(january.strftime('%m'))
    current_year = january.strftime('%Y')
    ozon_marketplace = CodingMarketplaces.objects.get(marketpalce='Ozon')
    for article in article_data:
        article_data = OzonSales.objects.filter(
            offer_id=article.ozon_seller_article, month=january_month, year=current_year).values('total', 'quantity')
        summ_money = 0
        quantity = 0
        for i in article_data:
            quantity += i['quantity']
            summ_money += i['total']
        Selling(
            lighter=article,
            ur_lico=article.company,
            year=current_year,
            month=january_month,
            summ=summ_money,
            quantity=quantity,
            data=date,
            marketplace=ozon_marketplace).save()


def motivation_article_type_excel_file_export(data):
    """Создает и скачивает excel файл"""
    # Создаем DataFrame из данных
    wb = Workbook()
    # Получаем активный лист
    ws = wb.active

    # Заполняем лист данными
    for row, item in enumerate(data, start=2):
        ws.cell(row=row, column=1, value=str(item['common_article']))
        ws.cell(row=row, column=2, value=str(item['company']))
        if item['designer_article'] == False:
            ws.cell(row=row, column=3, value='')
        else:
            ws.cell(row=row, column=3, value=str(item['designer_article']))
        if item['copy_right'] == False:
            ws.cell(row=row, column=4, value='')
        else:
            ws.cell(row=row, column=4, value=str(item['copy_right']))
    # Устанавливаем заголовки столбцов
    ws.cell(row=1, column=1, value='Артикул')
    ws.cell(row=1, column=2, value='Компания')
    ws.cell(row=1, column=3, value='Дизайнерский ночник')
    ws.cell(row=1, column=4, value='С правами')

    al = Alignment(horizontal="center",
                   vertical="center")
    al_left = Alignment(horizontal="left",
                        vertical="center")
    thin = Side(border_style="thin", color="000000")

    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 10
    ws.column_dimensions['C'].width = 10
    ws.column_dimensions['D'].width = 10

    for i in range(len(data)+1):
        for c in ws[f'A{i+1}:D{i+1}']:
            for i in range(4):
                c[i].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[i].alignment = al_left

    # Сохраняем книгу Excel в память
    response = HttpResponse(content_type='application/xlsx')
    name = f'Article_type_{datetime.now().strftime("%Y.%m.%d")}.xlsx'
    file_data = 'attachment; filename=' + name
    response['Content-Disposition'] = file_data
    wb.save(response)

    return response


def motivation_article_type_excel_import(xlsx_file, ur_lico):
    """Импортирует данные о группе артикула из Excel"""
    excel_data_common = pd.read_excel(xlsx_file)
    column_list = excel_data_common.columns.tolist()
    if 'Артикул' in column_list and 'Дизайнерский ночник' in column_list and 'С правами' in column_list:
        excel_data = pd.DataFrame(excel_data_common, columns=[
                                  'Артикул', 'Дизайнерский ночник', 'С правами'])
        article_list = excel_data['Артикул'].to_list()
        designer_type_list = excel_data['Дизайнерский ночник'].to_list()
        copyright_type_list = excel_data['С правами'].to_list()

        # Словарь {артикул: название_группы}
        article_value_dict = {}
        # Список для обновления строк в БД
        new_objects = []

        for i in range(len(article_list)):
            article_value_dict[article_list[i]] = [
                designer_type_list[i], copyright_type_list[i]]

        for row in range(len(article_list)):
            if Articles.objects.filter(
                    company=ur_lico, common_article=article_list[row]).exists():
                article_obj = Articles.objects.get(
                    company=ur_lico, common_article=article_list[row])
                if str(article_value_dict[article_list[row]][0]).capitalize() == 'True':
                    article_obj.designer_article = True
                    if str(article_value_dict[article_list[row]][1]) == 'True':
                        article_obj.copy_right = True
                    else:
                        article_obj.copy_right = False
                else:
                    article_obj.designer_article = False
                    article_obj.copy_right = False

                new_objects.append(article_obj)
        Articles.objects.bulk_update(
            new_objects, ['designer_article', 'copy_right'])
    else:
        return f'Вы пытались загрузить ошибочный файл {xlsx_file}.'
