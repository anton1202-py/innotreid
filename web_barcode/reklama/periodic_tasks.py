import json
import math
import os
import time
from datetime import datetime, timedelta

import requests
import telegram
# from celery_tasks.celery import app
from dotenv import load_dotenv
from price_system.supplyment import sender_error_to_tg
from reklama.models import (AdvertisingCampaign, CompanyStatistic,
                            ProcentForAd, SalesArticleStatistic,
                            WbArticleCommon, WbArticleCompany)

# Загрузка переменных окружения из файла .env
dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)


REFRESH_TOKEN_DB = os.getenv('REFRESH_TOKEN_DB')
APP_KEY_DB = os.getenv('APP_KEY_DB')
APP_SECRET_DB = os.getenv('APP_SECRET_DB')

API_KEY_WB_IP = os.getenv('API_KEY_WB_IP')
YANDEX_IP_KEY = os.getenv('YANDEX_IP_KEY')
API_KEY_OZON_KARAVAEV = os.getenv('API_KEY_OZON_KARAVAEV')
CLIENT_ID_OZON_KARAVAEV = os.getenv('CLIENT_ID_OZON_KARAVAEV')

OZON_OOO_API_TOKEN = os.getenv('OZON_OOO_API_TOKEN')
OZON_OOO_CLIENT_ID = os.getenv('OZON_OOO_CLIENT_ID')
YANDEX_OOO_KEY = os.getenv('YANDEX_OOO_KEY')
WB_OOO_API_KEY = os.getenv('WB_OOO_API_KEY')


TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID_ADMIN = os.getenv('CHAT_ID_ADMIN')
CHAT_ID_MANAGER = os.getenv('CHAT_ID_MANAGER')
CHAT_ID_EU = os.getenv('CHAT_ID_EU')
CHAT_ID_AN = os.getenv('CHAT_ID_AN')

bot = telegram.Bot(token=TELEGRAM_TOKEN)

wb_headers_karavaev = {
    'Content-Type': 'application/json',
    'Authorization': API_KEY_WB_IP
}
wb_headers_ooo = {
    'Content-Type': 'application/json',
    'Authorization': WB_OOO_API_KEY
}

ozon_headers_karavaev = {
    'Api-Key': API_KEY_OZON_KARAVAEV,
    'Content-Type': 'application/json',
    'Client-Id': CLIENT_ID_OZON_KARAVAEV
}
ozon_headers_ooo = {
    'Api-Key': OZON_OOO_API_TOKEN,
    'Content-Type': 'application/json',
    'Client-Id': OZON_OOO_CLIENT_ID
}

yandex_headers_karavaev = {
    'Authorization': YANDEX_IP_KEY,
}
yandex_headers_ooo = {
    'Authorization': YANDEX_OOO_KEY,
}

wb_header = {
    'ООО Иннотрейд': wb_headers_ooo,
    'ИП Караваев': wb_headers_karavaev
}


def create_articles_company(campaign_number, header):
    """При создании кампании записываются артикулы этой кампании в базу"""
    url = 'https://advert-api.wb.ru/adv/v1/promotion/adverts'
    payload = json.dumps([
        campaign_number
    ])
    response = requests.request("POST", url, headers=header, data=payload)
    articles_list = json.loads(response.text)[0]['autoParams']['nms']
    for article in articles_list:
        if not WbArticleCommon.objects.filter(wb_article=article).exists():
            WbArticleCommon(wb_article=article).save()
        campaign_obj = AdvertisingCampaign.objects.get(
            campaign_number=campaign_number)
        article_obj = WbArticleCommon.objects.get(wb_article=article)
        WbArticleCompany(
            campaign_number=campaign_obj,
            wb_article=article_obj
        ).save()


@sender_error_to_tg
# @app.task
def ad_list():
    """
    Достает список номеров всех компании из базы данных.
    """
    campaign_data = AdvertisingCampaign.objects.all().values()
    campaign_list = []
    for i in campaign_data:
        campaign_list.append(int(i['campaign_number']))
    return campaign_list


# @sender_error_to_tg
def db_articles_in_campaign(campaign_number):
    """Достает артикулы, которые есть у компании в базе данных"""
    campaign_obj = AdvertisingCampaign.objects.get(
        campaign_number=campaign_number)
    articles_data = WbArticleCompany.objects.filter(
        campaign_number=campaign_obj
    )
    articles_list = []
    for data in articles_data:
        articles_list.append(int(data.wb_article.wb_article))

    return articles_list


# @sender_error_to_tg
def wb_articles_in_campaign(campaign_number, header):
    """Достает артикулы, которые есть у компании в Wildberries"""
    url = 'https://advert-api.wb.ru/adv/v1/promotion/adverts'
    payload = json.dumps([
        campaign_number
    ])
    response = requests.request("POST", url, headers=header, data=payload)
    articles_list = json.loads(response.text)[0]['autoParams']['nms']
    return articles_list

# @sender_error_to_tg


def header_determinant(campaign_number):
    """Определяет какой header использовать"""
    header_common = AdvertisingCampaign.objects.get(
        campaign_number=campaign_number).ur_lico.ur_lice_name
    header = wb_header[header_common]

    return header


# @sender_error_to_tg
# @app.task
def campaign_article_add():
    """
    Сравнивает списки артикулов в рекламной кампании WB и в рекламной кампании
    базы данных. Если есть расхождения - устранияет их.
    """
    campaign_list = ad_list()
    # Сравниваю данные для каждой кампании между ВБ и Базой ДАнных.
    # Если есть расхождения, устранияю их в базе данных
    for campaign in campaign_list:
        header = header_determinant(campaign)
        campaign_obj = AdvertisingCampaign.objects.get(
            campaign_number=campaign)
        # Смотрю список артикулов на ВБ
        wb_articles_list = wb_articles_in_campaign(campaign, header)
        db_articles_list = db_articles_in_campaign(campaign)
        # Если артикула нет в базе - добавляем
        for article in wb_articles_list:
            if article not in db_articles_list:
                if not WbArticleCommon.objects.filter(wb_article=article).exists():
                    WbArticleCommon(wb_article=article).save()

                article_obj = WbArticleCommon.objects.get(wb_article=article)
                WbArticleCompany(
                    campaign_number=campaign_obj,
                    wb_article=article_obj
                ).save()
        # Если артикула из базы нет в ВБ - удаляем
        for db_article in db_articles_list:
            if db_article not in wb_articles_list:
                article_obj = WbArticleCommon.objects.get(
                    wb_article=db_article)
                wb = WbArticleCompany.objects.filter(
                    campaign_number=campaign_obj,
                    wb_article=article_obj
                )
                # print(wb)
                print('Удалил артикул', article)


def count_sum_adv_campaign(data_list: list):
    """
    Подсчитывает сумму в рублях одной рекламной кампании
    data_list - входящий список данных по артикулвм в кампании
    """
    sum = 0

    for data in data_list:
        article_sum = data['statistics']['selectedPeriod']['ordersSumRub']
        sum += article_sum
    return sum


def count_sum_orders():
    """Считает сумму заказов каждой рекламной кампании за позавчера"""
    campaign_list = ad_list()

    calculate_data = datetime.now() - timedelta(days=2)
    begin_date = calculate_data.strftime('%Y-%m-%d 00:00:00')
    end_date = calculate_data.strftime('%Y-%m-%d 23:59:59')
    # Словарь вида: {номер_компании: заказов_за_позавчера}
    url = 'https://suppliers-api.wildberries.ru/content/v1/analytics/nm-report/detail'
    campaign_orders_money_dict = {}
    for campaign in campaign_list:
        header = header_determinant(campaign)
        article_list = wb_articles_in_campaign(campaign, header)
        payload = json.dumps({
            "brandNames": [],
            "objectIDs": [],
            "tagIDs": [],
            "nmIDs": article_list,
            "timezone": "Europe/Moscow",
            "period": {
                "begin": begin_date,
                "end": end_date
            },
            "orderBy": {
                "field": "ordersSumRub",
                "mode": "asc"
            },
            "page": 1
        })
        response = requests.request("POST", url, headers=header, data=payload)

        data_list = json.loads(response.text)['data']['cards']
        sum = count_sum_adv_campaign(data_list)
        campaign_orders_money_dict[campaign] = sum
    print(campaign_orders_money_dict)
    return campaign_orders_money_dict


def replenish_campaign_budget(campaign, budget, header):
    """Пополняет бюджет рекламной кампаний"""
    url = f'https://advert-api.wb.ru/adv/v1/budget/deposit?id={campaign}'
    campaign_obj = AdvertisingCampaign.objects.get(campaign_number=campaign)
    koef = ProcentForAd.objects.get(
        campaign_number=campaign_obj
    ).koefficient
    campaign_budget = math.ceil(budget * koef / 100)

    if campaign_budget < 500:
        campaign_budget = 500
    elif campaign_budget > 10000:
        campaign_budget = 10000

    payload = json.dumps({
        "sum": campaign_budget,
        "type": 1,
        "return": True
    })
    print(campaign_budget)
    response = requests.request("POST", url, headers=header, data=payload)
    message = f"Пополнил бюджет кампании {campaign} на {campaign_budget}. Итого сумма: {response.text}"
    bot.send_message(chat_id=CHAT_ID_ADMIN,
                     text=message, parse_mode='HTML')


def budget_working():
    """Работа с бюджетом компании"""
    campaign_data = count_sum_orders()
    for campaign, budget in campaign_data.items():
        header = header_determinant(campaign)
        replenish_campaign_budget(campaign, budget, header)
        time.sleep(2)
