import json
import math
import os
import time
from datetime import datetime, timedelta

import requests
import telegram
from database.models import CodingMarketplaces, OzonSales, WildberriesSales
from django.contrib.auth.models import User
# from celery_tasks.celery import app
from dotenv import load_dotenv
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


def designer_data_merge():
    main_data = User.objects.all()
    for data in main_data:
        print(data)
        DesignUser(
            designer=data
        ).save()
    print(len(main_data))


def get_current_selling():
    """Получаем текущие продажи артикулов"""
    # ozon_sale_data = OzonSales.objects.all()
    article_data = Articles.objects.all()
    date = datetime.now()
    january = date - timedelta(days=110)
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
