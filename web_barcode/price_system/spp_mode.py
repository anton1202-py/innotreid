import json
import time

import requests
import telegram

from web_barcode.constants_file import (CHAT_ID_ADMIN, TELEGRAM_TOKEN,
                                        header_ozon_dict, header_wb_data_dict,
                                        header_wb_dict, header_yandex_dict,
                                        wb_headers_karavaev, wb_headers_ooo,
                                        yandex_business_id_dict)

from .models import ArticleGroup, Articles, ArticlesPrice, Groups
from .supplyment import sender_error_to_tg

bot = telegram.Bot(token=TELEGRAM_TOKEN)


@sender_error_to_tg
def wb_discounts_prices_single_article_info(header, article, counter=0):
    """Получаем данные одного артикула ВБ"""
    url = f'https://discounts-prices-api.wb.ru/api/v2/list/goods/filter?limit=1000&filterNmID={article}'
    response = requests.request("GET", url, headers=header)
    counter += 1
    print(response.status_code, article, counter)
    if response.status_code == 200:
        main_data = json.loads(response.text)['data']['listGoods']
        return main_data
    else:
        time.sleep(10)
        if counter < 10:
            return wb_discounts_prices_single_article_info(header, article, counter)
        else:
            return {}


@sender_error_to_tg
def return_article_discount_price_info(ur_lico, article):
    """Возвращает данные о цене и скидке артикула"""
    header = header_wb_dict[ur_lico]
    main_data = wb_discounts_prices_single_article_info(header, article)
    data_dict = {}
    if main_data:
        for data in main_data:
            data_dict['nmId'] = data['nmID']
            data_dict['price'] = data['sizes'][0]['price']
            data_dict['discount'] = data['discount']
    return data_dict


@sender_error_to_tg
def price_group_article_info():
    """Получаем список словарей с группой цен, первым артикулом в ней и юр лицом группы"""
    main_db_data = Groups.objects.all().values_list('id', 'name', 'company')
    # Словарь вида {group_ogj: nm_id}
    group_nmid_list = []
    # находим по первому артикулу в каждой ценовой группе
    for group_data in main_db_data:
        group_obj = Groups.objects.get(id=group_data[0])

        article = ArticleGroup.objects.filter(group=group_obj)
        inner_dict = {}
        if article.exists():
            inner_dict['group_object'] = group_obj
            inner_dict['wb_nmid'] = article[0].common_article.wb_nomenclature
            inner_dict['ur_lico'] = group_data[2]
            group_nmid_list.append(inner_dict)
    return group_nmid_list


@sender_error_to_tg
def get_front_api_wb_info(nm_id, ur_lico, group_object):
    """
    Получаем цену артикула на странице ВБ от api фронта ВБ
    nm_id - номенклатурный номер артикула на WB
    ur_lico - юр лицо, которому принадлежит артикул
    group_object - объект группы цен, в которой находится артикул
    """
    url = f'https://card.wb.ru/cards/detail?appType=0&curr=rub&dest=-446085&regions=80,83,38,4,64,33,68,70,30,40,86,75,69,1,66,110,22,48,31,71,112,114&spp=99&nm={nm_id}'
    response = requests.request(
        "GET", url)
    data = json.loads(response.text)
    price = ''
    if data['data']['products']:
        price = int(data['data']['products'][0]
                                ['salePriceU'])//100
        return price
    else:
        if response.status_code == 200:
            article_obj = Articles.objects.get(
                company=ur_lico, wb_nomenclature=nm_id)
            ArticleGroup.objects.get(
                common_article=article_obj, group=group_object).delete()
            ArticlesPrice.objects.filter(common_article=article_obj).delete()
        message = f'{ur_lico} Не смог определить цену артикула {nm_id} через фронт апи ВБ. Статус код {response.status_code}'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message, parse_mode='HTML')
        return 0


@sender_error_to_tg
def calculate_spp(price_from_page, price_from_wb_api, discount_from_wb_api):
    """Считает СПП артикула"""
    spp = int((1 - (price_from_page/price_from_wb_api /
                    (1 - discount_from_wb_api/100))) * 100)
    return spp


@sender_error_to_tg
def article_spp_info():
    """
    Получает СПП для каждой группы цен.
    Возвращает словарь типа: {group_obj: spp}
    """
    group_db_data = price_group_article_info()
    group_spp_data_dict = {}
    for group_data in group_db_data:
        ur_lico = group_data['ur_lico']
        article = group_data['wb_nmid']
        group_object = group_data['group_object']
        article_info = return_article_discount_price_info(ur_lico, article)

        price_from_page = get_front_api_wb_info(article, ur_lico, group_object)
        if article_info:
            price_from_wb_api = article_info['price']
            discount_from_wb_api = article_info['discount']
            if price_from_page != 0:
                spp = calculate_spp(
                    price_from_page, price_from_wb_api, discount_from_wb_api)
                group_spp_data_dict[group_object] = spp
    return group_spp_data_dict
