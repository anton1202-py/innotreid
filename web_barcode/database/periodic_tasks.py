import json
import math
import os
import time
from datetime import datetime, timedelta

from api_request.ozon_requests import (ozon_orsers_daily_report,
                                       ozon_sales_monthly_report)
from api_request.wb_requests import wb_sales_statistic
from api_request.yandex_requests import yandex_daily_orders
from celery_tasks.celery import app
from django.contrib.auth.models import User
from dotenv import load_dotenv
from price_system.models import Articles, DesignUser
from price_system.supplyment import sender_error_to_tg

from web_barcode.constants_file import (CHAT_ID_ADMIN, TELEGRAM_TOKEN, bot,
                                        header_ozon_dict, header_wb_data_dict,
                                        header_wb_dict, header_yandex_dict,
                                        ozon_adv_client_secret_dict,
                                        ozon_api_token_dict,
                                        wb_headers_karavaev, wb_headers_ooo,
                                        yandex_business_id_dict,
                                        yandex_campaign_id_dict_list,
                                        yandex_fbs_campaign_id_dict)

from .models import WildberriesSales
from .ozon_supplyment import (ozon_main_process_sale_data,
                              save_ozon_daily_orders,
                              save_ozon_daily_orders_data_for_motivation,
                              save_ozon_sale_data_for_motivation)
from .wb_supplyment import (save_wildberries_sale_data_for_motivation,
                            wb_save_sales_data_to_database)
from .yandex_supplyment import (save_yandex_daily_orders,
                                save_yandex_daily_orders_data_for_motivation)


@app.task
def process_wb_sales_data():
    """Записывает данные по продажам WB в базу данных. Ежедневно. Раз в сутки."""
    nessesary_date = datetime.now() - timedelta(days=2)
    check_date = nessesary_date.strftime('%Y-%m-%d')
    month_report = int(nessesary_date.strftime('%m'))
    year_report = nessesary_date.strftime('%Y')
    for ur_lico, header in header_wb_dict.items():
        main_data = wb_sales_statistic(header, check_date)
        for data in main_data:
            wb_save_sales_data_to_database(
                data, ur_lico, month_report, year_report)
            save_wildberries_sale_data_for_motivation(
                data, ur_lico, month_report, year_report)
        time.sleep(65)


@app.task
def process_ozon_daily_orders():
    """Записывает данные по заказам Озон в базу данных. Ежедневно. Раз в сутки."""
    nessesary_date = datetime.now() - timedelta(days=2)
    check_date = nessesary_date.strftime('%Y-%m-%d')
    month_report = int(nessesary_date.strftime('%m'))
    year_report = nessesary_date.strftime('%Y')
    for ur_lico, header in header_ozon_dict.items():
        main_data = ozon_orsers_daily_report(header, check_date)
        for data in main_data['result']['data']:
            save_ozon_daily_orders(
                data, check_date, month_report, year_report, ur_lico)
            save_ozon_daily_orders_data_for_motivation(
                data, check_date, month_report, year_report, ur_lico)
            # time.sleep(1)
        time.sleep(65)


@app.task
def process_yandex_daily_orders():
    """Записывает данные по заказам Яндекс в базу данных. Ежедневно. Раз в сутки."""
    nessesary_date = datetime.now() - timedelta(days=4)
    check_date = nessesary_date.strftime('%Y-%m-%d')
    month_report = int(nessesary_date.strftime('%m'))
    year_report = nessesary_date.strftime('%Y')
    for ur_lico, header in header_yandex_dict.items():
        for campaign_id_dict in yandex_campaign_id_dict_list:
            main_data = yandex_daily_orders(
                header, campaign_id_dict[ur_lico], check_date)
            if main_data['result']['orders']:
                for data in main_data['result']['orders']:
                    save_yandex_daily_orders(
                        data, check_date, month_report, year_report, ur_lico)
                    save_yandex_daily_orders_data_for_motivation(
                        data, check_date, month_report, year_report, ur_lico)
                    # time.sleep(1)
                time.sleep(65)


@app.task
def process_ozon_sales_data():
    """Записывает данные по продажам Ozon в базу данных. Включается 10 числа каждого месяца"""
    nessesary_date = datetime.now() - timedelta(days=20)
    month_report = int(nessesary_date.strftime('%m'))
    year_report = nessesary_date.strftime('%Y')
    for ur_lico, header in header_ozon_dict.items():
        main_data = ozon_sales_monthly_report(
            header, month_report, year_report)
        ozon_main_process_sale_data(
            main_data, ur_lico, month_report, year_report)
        time.sleep(65)
    message = 'Сохранил продажи Озон за предыдущий месяц'
    bot.send_message(chat_id=CHAT_ID_ADMIN, text=message)
