import io
import json
import os
import sys
import time
from contextlib import closing
from datetime import date, datetime, timedelta
from time import sleep

import dropbox
import pandas as pd
import psycopg2
import requests
import telegram
from django.conf import settings
# from celery_tasks.celery import app
from dotenv import load_dotenv
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
bot = telegram.Bot(token=TELEGRAM_TOKEN)
now_day = date.today()


class YandexMarketFbsMode():
    """Класс отвечает за работу с заказами Wildberries"""

    def __init__(self):
        """Основные данные класса"""
        self.amount_articles = {}
        self.dropbox_main_fbs_folder = '/DATABASE/beta'

    def check_folder_exists(self, path):
        try:
            dbx_db.files_list_folder(path)
            return True
        except dropbox.exceptions.ApiError as e:
            return False


url = "https://api.partner.market.yandex.ru/campaigns/23746359/orders?status=PROCESSING&substatus=STARTED"

payload = {}
headers = {
    'Authorization': 'Bearer y0_AgAEA7qjt7KxAApPWwAAAADpxzharlAhWWWhR-CN6aC7F0W9cZImPgo',
}
response = requests.request("GET", url, headers=headers, data=payload)

orders_list = json.loads(response.text)['orders']

main_orders_list = []
for order in orders_list:
    print(order)
    order_dict = {}
    article_list_in_order = order['items']
    inner_article_list = []
    for article in article_list_in_order:

        inner_article_dict = {}

        inner_article_dict['seller_article'] = article['offerId']
        inner_article_dict['article_name'] = article['offerName']
        inner_article_dict['amount'] = article['count']

        inner_article_list.append(inner_article_dict)

    order_dict[order['id']] = inner_article_list
    main_orders_list.append(order_dict)
print(main_orders_list)
