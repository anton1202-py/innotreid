from datetime import datetime

from celery_tasks.celery import app
from price_system.models import Articles, ArticlesPrice
from price_system.spp_mode import article_spp_info
from price_system.supplyment import (ozon_articles_list,
                                     ozon_matching_articles,
                                     sender_error_to_tg, wb_articles_list,
                                     wb_matching_articles,
                                     yandex_articles_list,
                                     yandex_matching_articles)

from web_barcode.constants_file import bot, spp_group_list

spp_group_list


@sender_error_to_tg
def wb_add_price_info(ur_lico):
    """
    Проверяет изменилась ли цена в базе данных.
    Если изменилась, то записывает новую цену.
    """
    wb_article_price_data = wb_articles_list(ur_lico)
    if wb_article_price_data:
        for data in wb_article_price_data:
            # Проверяем, существует ли запись в БД с таким ном номером (отсекаем грамоты)
            if Articles.objects.filter(company=ur_lico, wb_nomenclature=data['nmId']).exists():
                if ArticlesPrice.objects.filter(
                    common_article=Articles.objects.filter(company=ur_lico,
                                                           wb_nomenclature=data['nmId'])[0],
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
    for data in ozon_article_price_data:
        # Проверяем, существует ли запись в БД с таким ном номером (отсекаем грамоты)
        if Articles.objects.filter(company=ur_lico, ozon_product_id=data['product_id']).exists():
            if ArticlesPrice.objects.filter(
                common_article=Articles.objects.filter(company=ur_lico,
                                                       ozon_product_id=data['product_id'])[0],
                marketplace='Ozon'
            ).exists():
                latest_record = ArticlesPrice.objects.filter(
                    common_article=Articles.objects.filter(
                        ozon_product_id=data['product_id'])[0],
                    marketplace='Ozon'
                ).latest('id')
                if latest_record.price != int(float(data['price']['price'])):
                    ArticlesPrice(
                        common_article=Articles.objects.filter(
                            ozon_product_id=data['product_id'])[0],
                        marketplace='Ozon',
                        price_date=datetime.now().strftime('%Y-%m-%d'),
                        price=int(float(data['price']['price'])),
                    ).save()
            else:
                ArticlesPrice(
                    common_article=Articles.objects.filter(
                        ozon_product_id=data['product_id'])[0],
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
        if Articles.objects.filter(company=ur_lico, yandex_seller_article=data['offer']['offerId']).exists():
            if ArticlesPrice.objects.filter(
                common_article=Articles.objects.filter(company=ur_lico,
                                                       yandex_seller_article=data['offer']['offerId'])[0],
                marketplace='Yandex'
            ).exists():
                latest_record = ArticlesPrice.objects.filter(
                    common_article=Articles.objects.filter(company=ur_lico,
                                                           yandex_seller_article=data['offer']['offerId'])[0],
                    marketplace='Yandex'
                ).latest('id')
                if latest_record.price != data['offer']['basicPrice']['value']:
                    ArticlesPrice(
                        common_article=Articles.objects.filter(company=ur_lico,
                                                               yandex_seller_article=data['offer']['offerId'])[0],
                        marketplace='Yandex',
                        price_date=datetime.now().strftime('%Y-%m-%d'),
                        price=data['offer']['basicPrice']['value'],
                    ).save()
            else:
                ArticlesPrice(
                    common_article=Articles.objects.filter(company=ur_lico,
                                                           yandex_seller_article=data['offer']['offerId'])[0],
                    marketplace='Yandex',
                    price_date=datetime.now().strftime('%Y-%m-%d'),
                    price=data['offer']['basicPrice']['value'],
                ).save()


@app.task
def common_yandex_add_price_info():
    """
    Проверяет изменилась ли цена в базе данных на артикул YANDEX.
    Если изменилась, то записывает новую цену.
    """
    yandex_add_price_info('ИП Караваев')
    yandex_add_price_info('ООО Иннотрейд')


@app.task
def periodic_compare_ip_articles():
    """Сверка артикулов ИП"""
    wb_matching_articles('ИП Караваев')
    ozon_matching_articles('ИП Караваев')
    yandex_matching_articles('ИП Караваев')


@app.task
def periodic_compare_articles():
    """Сверка артикулов"""
    wb_matching_articles('ООО Иннотрейд')
    ozon_matching_articles('ООО Иннотрейд')
    yandex_matching_articles('ООО Иннотрейд')

    wb_matching_articles('ИП Караваев')
    ozon_matching_articles('ИП Караваев')
    yandex_matching_articles('ИП Караваев')

    wb_matching_articles('ООО Мастерская чудес')
    ozon_matching_articles('ООО Мастерская чудес')
    yandex_matching_articles('ООО Мастерская чудес')


@app.task
def write_group_spp_data():
    """Записывает в базу данных информацию об СПП ценовой группы"""
    time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    main_info = article_spp_info()
    if main_info:
        for group_obj, spp in main_info.items():
            if group_obj.spp != spp:
                message = f'SPP группы {group_obj.name} изменилась. Была {group_obj.spp}, стала - {spp}'

                group_obj.spp = spp
                group_obj.change_date_spp = time_now
                group_obj.save()

                for chat_id in spp_group_list:
                    bot.send_message(chat_id=chat_id,
                                     text=message, parse_mode='HTML')
