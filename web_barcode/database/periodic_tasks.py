import json
import math
import os
import time
from datetime import datetime, timedelta

import requests
import telegram
from api_request.ozon_requests import ozon_sales_monthly_report
from api_request.wb_requests import wb_sales_statistic
from django.contrib.auth.models import User
# from celery_tasks.celery import app
from dotenv import load_dotenv
from price_system.models import Articles, DesignUser
from price_system.supplyment import sender_error_to_tg

from web_barcode.constants_file import (CHAT_ID_ADMIN, TELEGRAM_TOKEN, bot,
                                        header_ozon_dict, header_wb_data_dict,
                                        header_wb_dict, header_yandex_dict,
                                        ozon_adv_client_access_id_dict,
                                        ozon_adv_client_secret_dict,
                                        ozon_api_token_dict,
                                        wb_headers_karavaev, wb_headers_ooo,
                                        yandex_business_id_dict)

from .models import WildberriesSales
from .ozon_supplyment import ozon_main_process_sale_data
from .wb_supplyment import wb_save_sales_data_to_database


def process_wb_sales_data():
    """Записывает данные по продажам WB в базу данных"""
    nessesary_date = datetime.now() - timedelta(days=2)
    check_date = nessesary_date.strftime('%Y-%m-%d')
    month_report = int(nessesary_date.strftime('%m'))
    year_report = nessesary_date.strftime('%Y')
    for ur_lico, header in header_wb_dict.items():
        main_data = wb_sales_statistic(header, check_date)
        for data in main_data:
            wb_save_sales_data_to_database(
                data, ur_lico, month_report, year_report)
        time.sleep(65)


def process_ozon_sales_data():
    """Записывает данные по продажам Ozon в базу данных"""
    nessesary_date = datetime.now() - timedelta(days=100)
    month_report = int(nessesary_date.strftime('%m'))
    year_report = nessesary_date.strftime('%Y')
    print(month_report)
    for ur_lico, header in header_ozon_dict.items():
        print('ur_lico', ur_lico)
        main_data = ozon_sales_monthly_report(
            header, month_report, year_report)
        ozon_main_process_sale_data(
            main_data, ur_lico, month_report, year_report)
        time.sleep(65)
