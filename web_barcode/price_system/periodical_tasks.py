from datetime import datetime

from celery_tasks.celery import app
from price_system.models import ArticleGroup, Articles, ArticlesPrice, Groups
from price_system.supplyment import (applies_price_for_price_group,
                                     ozon_articles_list,
                                     ozon_matching_articles,
                                     sender_error_to_tg, wb_articles_list,
                                     wb_matching_articles,
                                     yandex_articles_list,
                                     yandex_matching_articles)
from reklama.models import UrLico

from web_barcode.constants_file import (CHAT_ID_ADMIN, admins_chat_id_list,
                                        bot, spp_group_list)


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
                        common_article=Articles.objects.filter(company=ur_lico,
                                                               wb_nomenclature=data['nmId'])[0],
                        marketplace='Wildberries'
                    ).latest('id')
                    if latest_record.price != data['price']:
                        ArticlesPrice(
                            common_article=Articles.objects.filter(company=ur_lico,
                                                                   wb_nomenclature=data['nmId'])[0],
                            marketplace='Wildberries',
                            price_date=datetime.now().strftime('%Y-%m-%d'),
                            price=data['price'],
                            basic_discount=data['discount']
                        ).save()
                else:
                    ArticlesPrice(
                        common_article=Articles.objects.filter(company=ur_lico,
                                                               wb_nomenclature=data['nmId'])[0],
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
    from price_system.spp_mode import article_spp_info
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


@app.task
def check_articles_without_pricegroup():
    """Проверяет, чтобы не было артикулов без группы цен"""
    ur_lico_list = UrLico.objects.all()

    for urlico_obj in ur_lico_list:
        group_data = ArticleGroup.objects.filter(common_article__company=urlico_obj.ur_lice_name,
                                                 group__isnull=True)
        empty_group_list = []
        for data in group_data:
            empty_group_list.append(data.common_article.common_article)

        message = f'У Юр. лица {urlico_obj.ur_lice_name} Артикулы, у которых нет группы: {empty_group_list}'
        for chat_id in admins_chat_id_list:
            bot.send_message(chat_id=chat_id,
                             text=message[:4000], parse_mode='HTML')


@app.task
def transfer_article_to_designer_group():
    """Переводит артикулы с правами в Лицензионную и Авторскую группу"""
    ur_lico_list = UrLico.objects.all()
    for urlico_obj in ur_lico_list:
        articles_data = Articles.objects.filter(
            company=urlico_obj.ur_lice_name)
        group_name_list = []
        for article_obj in articles_data:
            article_group = ArticleGroup.objects.get(
                common_article=article_obj).group
            if article_obj.copy_right == True:
                if article_group:
                    if urlico_obj.ur_lice_name == 'ООО Иннотрейд':
                        if 't' in article_obj.common_article and article_group.name != 'Лицензия':
                            article_group.name = 'Лицензия'
                        elif article_group.name != 'Авторские':
                            article_group.name = 'Авторские'
                    if urlico_obj.ur_lice_name == 'ИП Караваев':
                        if ArticleGroup.objects.get(common_article=article_obj).group.name != 'Ночник ИП авторский':
                            article_group.name = 'Ночник ИП авторский'
                else:
                    if urlico_obj.ur_lice_name == 'ООО Иннотрейд':
                        if 't' in article_obj.common_article:
                            article_group = Groups.objects.get(
                                company='ООО Иннотрейд', name='Лицензия')
                        else:
                            article_group = Groups.objects.get(
                                company='ООО Иннотрейд', name='Авторские')
                    if urlico_obj.ur_lice_name == 'ИП Караваев':
                        article_group = Groups.objects.get(
                            company='ИП Караваев', name='Ночник ИП авторский')
                article_group.save()
                group_name_list.append(article_group.name)

        # Применяем цены на группу
        for group_name in group_name_list:
            applies_price_for_price_group(group_name, urlico_obj.ur_lice_name)

        # message = f'У Юр. лица {urlico_obj.ur_lice_name} Артикулы, у которых нет группы: {empty_group_list}'
        # for chat_id in admins_chat_id_list:
        #     bot.send_message(chat_id=chat_id,
        #                      text=message[:4000], parse_mode='HTML')
