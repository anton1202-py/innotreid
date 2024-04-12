import json
import os
from datetime import datetime

import requests
import telegram
from celery_tasks.celery import app
from dotenv import load_dotenv
from price_system.models import Articles, ArticlesPrice
from price_system.supplyment import (ozon_articles_list,
                                     ozon_matching_articles,
                                     sender_error_to_tg, wb_articles_list,
                                     wb_matching_articles,
                                     yandex_articles_list,
                                     yandex_matching_articles)


@sender_error_to_tg
def wb_add_price_info(ur_lico):
    """
    Проверяет изменилась ли цена в базе данных.
    Если изменилась, то записывает новую цену.
    """
    wb_article_price_data = wb_articles_list(ur_lico)
    for data in wb_article_price_data:
        # Проверяем, существует ли запись в БД с таким ном номером (отсекаем грамоты)
        if Articles.objects.filter(wb_nomenclature=data['nmId']).exists():
            if ArticlesPrice.objects.filter(
                common_article=Articles.objects.get(
                    wb_nomenclature=data['nmId']),
                marketplace='Wildberries'
            ).exists():
                latest_record = ArticlesPrice.objects.filter(
                    common_article=Articles.objects.get(
                        wb_nomenclature=data['nmId']),
                    marketplace='Wildberries'
                ).latest('id')
                if latest_record.price != data['price']:
                    ArticlesPrice(
                        common_article=Articles.objects.get(
                            wb_nomenclature=data['nmId']),
                        marketplace='Wildberries',
                        price_date=datetime.now().strftime('%Y-%m-%d'),
                        price=data['price'],
                        basic_discount=data['discount']
                    ).save()
            else:
                ArticlesPrice(
                    common_article=Articles.objects.get(
                        wb_nomenclature=data['nmId']),
                    marketplace='Wildberries',
                    price_date=datetime.now().strftime('%Y-%m-%d'),
                    price=data['price'],
                    basic_discount=data['discount']
                ).save()


@app.task
def common_wb_add_price_info():
    """
    Проверяет изменилась ли цена в базе данных для ООО и ИП.
    Если изменилась, то записывает новую цену.
    """
    wb_add_price_info('ИП Караваев')
    wb_add_price_info('ООО Иннотрейд')


@sender_error_to_tg
def ozon_add_price_info(ur_lico):
    """
    Проверяет изменилась ли цена в базе данных на артикул ОЗОН.
    Если изменилась, то записывает новую цену.
    """
    ozon_article_price_data = ozon_articles_list(ur_lico)
    print('**************************')
    print('прошли ozon_article_price_data')
    for data in ozon_article_price_data:
        # Проверяем, существует ли запись в БД с таким ном номером (отсекаем грамоты)
        if Articles.objects.filter(ozon_product_id=data['product_id']).exists():
            if ArticlesPrice.objects.filter(
                common_article=Articles.objects.get(
                    ozon_product_id=data['product_id']),
                marketplace='Ozon'
            ).exists():
                latest_record = ArticlesPrice.objects.filter(
                    common_article=Articles.objects.get(
                        ozon_product_id=data['product_id']),
                    marketplace='Ozon'
                ).latest('id')
                if latest_record.price != int(float(data['price']['price'])):
                    ArticlesPrice(
                        common_article=Articles.objects.get(
                            ozon_product_id=data['product_id']),
                        marketplace='Ozon',
                        price_date=datetime.now().strftime('%Y-%m-%d'),
                        price=int(float(data['price']['price'])),
                    ).save()
            else:
                ArticlesPrice(
                    common_article=Articles.objects.get(
                        ozon_product_id=data['product_id']),
                    marketplace='Ozon',
                    price_date=datetime.now().strftime('%Y-%m-%d'),
                    price=int(float(data['price']['price'])),
                ).save()


@app.task
def common_ozon_add_price_info():
    """
    Проверяет изменилась ли цена в базе данных на артикул ОЗОН ООО и ИП.
    Если изменилась, то записывает новую цену.
    """
    ozon_add_price_info('ИП Караваев')
    ozon_add_price_info('ООО Иннотрейд')


@sender_error_to_tg
def yandex_add_price_info(ur_lico):
    """
    Проверяет изменилась ли цена в базе данных на артикул YANDEX.
    Если изменилась, то записывает новую цену.
    """
    yandex_article_price_data = yandex_articles_list(ur_lico)
    for data in yandex_article_price_data:
        # Проверяем, существует ли запись в БД с таким ном номером (отсекаем грамоты)
        if Articles.objects.filter(yandex_seller_article=data['offer']['offerId']).exists():
            if ArticlesPrice.objects.filter(
                common_article=Articles.objects.get(
                    yandex_seller_article=data['offer']['offerId']),
                marketplace='Yandex'
            ).exists():
                latest_record = ArticlesPrice.objects.filter(
                    common_article=Articles.objects.get(
                        yandex_seller_article=data['offer']['offerId']),
                    marketplace='Yandex'
                ).latest('id')
                if latest_record.price != data['offer']['basicPrice']['value']:
                    ArticlesPrice(
                        common_article=Articles.objects.get(
                            yandex_seller_article=data['offer']['offerId']),
                        marketplace='Yandex',
                        price_date=datetime.now().strftime('%Y-%m-%d'),
                        price=data['offer']['basicPrice']['value'],
                    ).save()
            else:
                ArticlesPrice(
                    common_article=Articles.objects.get(
                        yandex_seller_article=data['offer']['offerId']),
                    marketplace='Yandex',
                    price_date=datetime.now().strftime('%Y-%m-%d'),
                    price=data['offer']['basicPrice']['value'],
                ).save()


@app.task
def common_yandex_add_price_info():
    yandex_add_price_info('ИП Караваев')
    yandex_add_price_info('ООО Иннотрейд')


@app.task
def periodic_compare_ip_articles():
    wb_matching_articles('ИП Караваев')
    ozon_matching_articles('ИП Караваев')
    yandex_matching_articles('ИП Караваев')


@app.task
def periodic_compare_ooo_articles():
    wb_matching_articles('ООО Иннотрейд')
    ozon_matching_articles('ООО Иннотрейд')
    yandex_matching_articles('ООО Иннотрейд')
