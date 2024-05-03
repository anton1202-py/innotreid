import json
import math
import os
import time
from datetime import datetime, timedelta

import requests
import telegram
from api_request.wb_requests import wb_sales_statistic
from django.contrib.auth.models import User
# from celery_tasks.celery import app
# from celery_tasks.celery import app
from dotenv import load_dotenv
from price_system.models import Articles, DesignUser
from price_system.supplyment import sender_error_to_tg
from reklama.models import (AdvertisingCampaign, CompanyStatistic,
                            DataOooWbArticle, OooWbArticle, OzonCampaign,
                            ProcentForAd, SalesArticleStatistic,
                            WbArticleCommon, WbArticleCompany)

from web_barcode.constants_file import (CHAT_ID_ADMIN, TELEGRAM_TOKEN, bot,
                                        header_ozon_dict, header_wb_data_dict,
                                        header_wb_dict, header_yandex_dict,
                                        ozon_adv_client_access_id_dict,
                                        ozon_adv_client_secret_dict,
                                        ozon_api_token_dict,
                                        wb_headers_karavaev, wb_headers_ooo,
                                        yandex_business_id_dict)

from .models import OzonMonthlySalesData, OzonSales, WildberriesSales


def ozon_main_process_sale_data(main_data, ur_lico, month_report, year_report):
    """Обрабатывает главные данные отчета по продажам с Ozon"""
    print(len(main_data['result']['rows']))
    main_date_info = main_data['result']['header']
    # print('main_date_info', main_date_info)
    start_date_period = main_date_info['start_date']
    finish_date_period = main_date_info['stop_date']
    number_report = main_date_info['number']
    doc_date = main_date_info['doc_date']
    doc_amount = main_date_info['doc_amount']
    vat_amount = main_date_info['vat_amount']
    sale_article_info = main_data['result']['rows']

    main_sale_data_dict = {}
    main_sale_data_dict['start_date_period'] = start_date_period
    main_sale_data_dict['finish_date_period'] = finish_date_period
    main_sale_data_dict['number_report'] = number_report
    main_sale_data_dict['doc_date'] = doc_date
    main_sale_data_dict['doc_amount'] = doc_amount
    main_sale_data_dict['vat_amount'] = vat_amount
    main_sale_data_dict['ur_lico'] = ur_lico
    main_sale_data_dict['month'] = month_report
    main_sale_data_dict['year'] = year_report

    ozon_save_main_sale_data_in_database(main_sale_data_dict)
    ozon_article_sale_data(sale_article_info, ur_lico, start_date_period, finish_date_period,
                           number_report, month_report, year_report)


def ozon_article_sale_data(sale_article_info, ur_lico, start_date_period, finish_date_period,
                           number_report, month_report, year_report):
    """Обрабатывает данные артикулов отчета по продажам с Ozon"""
    for data in sale_article_info:
        func_data_dict = {}
        row_number = data['rowNumber']
        if row_number != 0:
            # print("row_number", row_number)
            offer_id = data['item']['offer_id']
            sku = data['item']['sku']
            barcode = data['item']['barcode']
            name = data['item']['name']

            seller_price_per_instance = data['seller_price_per_instance']

            amount = data['delivery_commission']['amount']
            bonus = data['delivery_commission']['bonus']
            commission = data['delivery_commission']['commission']
            compensation = data['delivery_commission']['compensation']
            price_per_instance = data['delivery_commission']['price_per_instance']
            quantity = data['delivery_commission']['quantity']
            standard_fee = data['delivery_commission']['standard_fee']
            stars = data['delivery_commission']['stars']
            total = data['delivery_commission']['total']

            commission_ratio = data['commission_ratio']

            if data['return_commission']:
                return_amount = data['return_commission']['amount']
                return_bonus = data['return_commission']['bonus']
                return_commission = data['return_commission']['commission']
                return_compensation = data['return_commission']['compensation']
                return_price_per_instance = data['return_commission']['price_per_instance']
                return_quantity = data['return_commission']['quantity']
                return_standard_fee = data['return_commission']['standard_fee']
                return_stars = data['return_commission']['stars']
                return_total = data['return_commission']['total']
            else:
                return_amount = None
                return_bonus = None
                return_commission = None
                return_compensation = None
                return_price_per_instance = None
                return_quantity = None
                return_standard_fee = None
                return_stars = None
                return_total = None

        func_data_dict['start_date_period'] = start_date_period
        func_data_dict['finish_date_period'] = finish_date_period
        func_data_dict['number_report'] = number_report
        func_data_dict['row_number'] = row_number
        func_data_dict['offer_id'] = offer_id
        func_data_dict['sku'] = sku
        func_data_dict['barcode'] = barcode
        func_data_dict['name'] = name
        func_data_dict['seller_price_per_instance'] = seller_price_per_instance
        func_data_dict['amount'] = amount
        func_data_dict['bonus'] = bonus
        func_data_dict['commission'] = commission
        func_data_dict['compensation'] = compensation
        func_data_dict['price_per_instance'] = price_per_instance
        func_data_dict['quantity'] = quantity
        func_data_dict['standard_fee'] = standard_fee
        func_data_dict['stars'] = stars
        func_data_dict['total'] = total
        func_data_dict['commission_ratio'] = commission_ratio
        func_data_dict['return_amount'] = return_amount
        func_data_dict['return_bonus'] = return_bonus
        func_data_dict['return_commission'] = return_commission
        func_data_dict['return_compensation'] = return_compensation
        func_data_dict['return_price_per_instance'] = return_price_per_instance
        func_data_dict['return_quantity'] = return_quantity
        func_data_dict['return_standard_fee'] = return_standard_fee
        func_data_dict['return_stars'] = return_stars
        func_data_dict['return_total'] = return_total
        func_data_dict['ur_lico'] = ur_lico,
        func_data_dict['month'] = month_report
        func_data_dict['year'] = year_report
        ozon_save_article_sale_in_database(func_data_dict)


def ozon_save_article_sale_in_database(func_data_dict):
    """Сохранет информацию о продажах артикула"""
    OzonSales(
        start_date_period=func_data_dict['start_date_period'],
        finish_date_period=func_data_dict['finish_date_period'],
        number_report=func_data_dict['number_report'],
        row_number=func_data_dict['row_number'],
        offer_id=func_data_dict['offer_id'],
        sku=func_data_dict['sku'],
        barcode=func_data_dict['barcode'],
        name=func_data_dict['name'],
        seller_price_per_instance=func_data_dict['seller_price_per_instance'],
        amount=func_data_dict['amount'],
        bonus=func_data_dict['bonus'],
        commission=func_data_dict['commission'],
        compensation=func_data_dict['compensation'],
        price_per_instance=func_data_dict['price_per_instance'],
        quantity=func_data_dict['quantity'],
        standard_fee=func_data_dict['standard_fee'],
        stars=func_data_dict['stars'],
        total=func_data_dict['total'],
        commission_ratio=func_data_dict['commission_ratio'],
        return_amount=func_data_dict['return_amount'],
        return_bonus=func_data_dict['return_bonus'],
        return_commission=func_data_dict['return_commission'],
        return_compensation=func_data_dict['return_compensation'],
        return_price_per_instance=func_data_dict['return_price_per_instance'],
        return_quantity=func_data_dict['return_quantity'],
        return_standard_fee=func_data_dict['return_standard_fee'],
        return_stars=func_data_dict['return_stars'],
        return_total=func_data_dict['return_total'],
        ur_lico=func_data_dict['ur_lico'],
        month=func_data_dict['month'],
        year=func_data_dict['year']
    ).save()


def ozon_save_main_sale_data_in_database(main_sale_data_dict):
    """Сохранет общую информацию о продажах за месяц"""
    OzonMonthlySalesData(
        start_date_period=main_sale_data_dict['start_date_period'],
        finish_date_period=main_sale_data_dict['finish_date_period'],
        number_report=main_sale_data_dict['number_report'],
        doc_date=main_sale_data_dict['doc_date'],
        doc_amount=main_sale_data_dict['doc_amount'],
        vat_amount=main_sale_data_dict['vat_amount'],
        month=main_sale_data_dict['month'],
        year=main_sale_data_dict['year'],
        ur_lico=main_sale_data_dict['ur_lico'],
    ).save()
