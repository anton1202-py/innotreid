import json
import os
from datetime import datetime

import requests
import telegram
from celery_tasks.celery import app
from dotenv import load_dotenv
from price_system.models import Articles, ArticlesPrice
from price_system.supplyment import sender_error_to_tg

# Загрузка переменных окружения из файла .env
dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)


API_KEY_WB_IP = os.getenv('API_KEY_WB_IP')
YANDEX_IP_KEY = os.getenv('YANDEX_IP_KEY')
API_KEY_OZON_KARAVAEV = os.getenv('API_KEY_OZON_KARAVAEV')
CLIENT_ID_OZON_KARAVAEV = os.getenv('CLIENT_ID_OZON_KARAVAEV')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID_ADMIN = os.getenv('CHAT_ID_ADMIN')

bot = telegram.Bot(token=TELEGRAM_TOKEN)

wb_headers_karavaev = {
    'Content-Type': 'application/json',
    'Authorization': API_KEY_WB_IP
}

ozon_headers_karavaev = {
    'Api-Key': API_KEY_OZON_KARAVAEV,
    'Content-Type': 'application/json',
    'Client-Id': CLIENT_ID_OZON_KARAVAEV
}

yandex_headers_karavaev = {
    'Authorization': YANDEX_IP_KEY,
}

@sender_error_to_tg
def wb_articles_list():
    """Получаем массив арткулов с ценами и скидками для ВБ"""
    url = 'https://suppliers-api.wildberries.ru/public/api/v1/info'
    response = requests.request("GET", url, headers=wb_headers_karavaev)
    if response.status_code == 200:
        article_price_data = json.loads(response.text)
        return article_price_data
    else:
        return wb_articles_list()



@sender_error_to_tg
@app.task
def wb_add_price_info():
    """
    Проверяет изменилась ли цена в базе данных.
    Если изменилась, то записывает новую цену.
    """
    wb_article_price_data = wb_articles_list()
    for data in wb_article_price_data:
        # Проверяем, существует ли запись в БД с таким ном номером (отсекаем грамоты)
        if Articles.objects.filter(wb_nomenclature=data['nmId']).exists():
            if ArticlesPrice.objects.filter(
                   common_article=Articles.objects.get(wb_nomenclature=data['nmId']),
                   marketplace='Wildberries'
                   ).exists():
                latest_record = ArticlesPrice.objects.filter(
                    common_article=Articles.objects.get(wb_nomenclature=data['nmId']),
                    marketplace='Wildberries'
                    ).latest('id')
                if latest_record.price != data['price']:
                    ArticlesPrice(
                        common_article=Articles.objects.get(wb_nomenclature=data['nmId']),
                        marketplace='Wildberries',
                        price_date=datetime.now().strftime('%Y-%m-%d'),
                        price=data['price'],
                        basic_discount=data['discount']
                    ).save()
            else:
                ArticlesPrice(
                    common_article=Articles.objects.get(wb_nomenclature=data['nmId']),
                    marketplace='Wildberries',
                    price_date=datetime.now().strftime('%Y-%m-%d'),
                    price=data['price'],
                    basic_discount=data['discount']
                ).save()

@sender_error_to_tg
def ozon_articles_list(last_id='', main_price_data=None):
    """Получаем массив арткулов с ценами и скидками для OZON"""
    if main_price_data is None:
        main_price_data = []
    url = 'https://api-seller.ozon.ru/v4/product/info/prices'
    payload = json.dumps({
      "filter": {
        "offer_id": [],
        "product_id": [],
        "visibility": "ALL"
      },
      "last_id": "",
      "limit": 1000
    })
    response = requests.request("POST", url, headers=ozon_headers_karavaev, data=payload)
    if response.status_code == 200:
        article_price_data = json.loads(response.text)['result']['items']
        for data in article_price_data:
            main_price_data.append(data)
        if len(article_price_data) == 1000:
            ozon_articles_list(json.loads(
                response.text)['result']['last_id'], main_price_data)
        return main_price_data
    else:
        return ozon_articles_list()



@sender_error_to_tg
@app.task
def ozon_add_price_info():
    """
    Проверяет изменилась ли цена в базе данных на артикул ОЗОН.
    Если изменилась, то записывает новую цену.
    """
    ozon_article_price_data = ozon_articles_list()
    for data in ozon_article_price_data:
        # Проверяем, существует ли запись в БД с таким ном номером (отсекаем грамоты)
        if Articles.objects.filter(ozon_product_id=data['product_id']).exists():
            if ArticlesPrice.objects.filter(
                common_article=Articles.objects.get(ozon_product_id=data['product_id']),
                marketplace='Ozon'
                ).exists():
                latest_record = ArticlesPrice.objects.filter(
                    common_article=Articles.objects.get(ozon_product_id=data['product_id']),
                    marketplace='Ozon'
                    ).latest('id')
                if latest_record.price != int(float(data['price']['price'])):
                    ArticlesPrice(
                        common_article=Articles.objects.get(ozon_product_id=data['product_id']),
                        marketplace='Ozon',
                        price_date=datetime.now().strftime('%Y-%m-%d'),
                        price=int(float(data['price']['price'])),
                    ).save()
            else:
                ArticlesPrice(
                    common_article=Articles.objects.get(ozon_product_id=data['product_id']),
                    marketplace='Ozon',
                    price_date=datetime.now().strftime('%Y-%m-%d'),
                    price=int(float(data['price']['price'])),
                ).save()

@sender_error_to_tg
def yandex_articles_list(page_token='', main_price_data=None):
    """Получаем массив арткулов с ценами и скидками для OZON"""
    if main_price_data is None:
        main_price_data = []
    url = f'https://api.partner.market.yandex.ru/businesses/3345369/offer-mappings?limit=200&page_token={page_token}'
    payload = json.dumps({
        "offerIds": [],
        "cardStatuses": [],
        "categoryIds": [],
        "vendorNames": [],
        "tags": [],
        "archived": False
    })
    response = requests.request("POST", url, headers=yandex_headers_karavaev, data=payload)
    if response.status_code == 200:
        article_price_data = json.loads(response.text)['result']['offerMappings']
        for data in article_price_data:
            main_price_data.append(data)
        if len(article_price_data) == 200:
            yandex_articles_list(json.loads(response.text)['result']['paging']['nextPageToken'], main_price_data)
        return main_price_data
    else:
        return yandex_articles_list()



@sender_error_to_tg
@app.task
def yandex_add_price_info():
    """
    Проверяет изменилась ли цена в базе данных на артикул YANDEX.
    Если изменилась, то записывает новую цену.
    """
    yandex_article_price_data = yandex_articles_list()
    for data in yandex_article_price_data:
        # Проверяем, существует ли запись в БД с таким ном номером (отсекаем грамоты)
        if Articles.objects.filter(yandex_seller_article=data['offer']['offerId']).exists():
            if ArticlesPrice.objects.filter(
                common_article=Articles.objects.get(yandex_seller_article=data['offer']['offerId']),
                marketplace='Yandex'
                ).exists():
                latest_record = ArticlesPrice.objects.filter(
                    common_article=Articles.objects.get(yandex_seller_article=data['offer']['offerId']),
                    marketplace='Yandex'
                    ).latest('id')
                if latest_record.price != data['offer']['basicPrice']['value']:
                    ArticlesPrice(
                        common_article=Articles.objects.get(yandex_seller_article=data['offer']['offerId']),
                        marketplace='Yandex',
                        price_date=datetime.now().strftime('%Y-%m-%d'),
                        price=data['offer']['basicPrice']['value'],
                    ).save()
            else:
                ArticlesPrice(
                    common_article=Articles.objects.get(yandex_seller_article=data['offer']['offerId']),
                    marketplace='Yandex',
                    price_date=datetime.now().strftime('%Y-%m-%d'),
                    price=data['offer']['basicPrice']['value'],
                ).save()
