import json
import math
import os
import time
from datetime import datetime, timedelta

import requests
import telegram
# from celery_tasks.celery import app
from dotenv import load_dotenv
from price_system.models import ArticleGroup
from price_system.supplyment import sender_error_to_tg
from reklama.models import (AdvertisingCampaign, CompanyStatistic,
                            DataOooWbArticle, OooWbArticle, OzonCampaign,
                            ProcentForAd, SalesArticleStatistic,
                            WbArticleCommon, WbArticleCompany)

from web_barcode.constants_file import (CHAT_ID_ADMIN, CHAT_ID_EU,
                                        TELEGRAM_TOKEN, admins_chat_id_list,
                                        bot, header_ozon_dict,
                                        header_wb_data_dict, header_wb_dict,
                                        header_yandex_dict,
                                        wb_headers_karavaev, wb_headers_ooo,
                                        yandex_business_id_dict)


@sender_error_to_tg
def get_actions_list(header):
    """Получает список акций юр. лица."""
    url = 'https://api-seller.ozon.ru/v1/actions'
    headers = header
    response = requests.request("GET", url, headers=headers)
    actions_list = []
    if response.status_code == 200:
        main_data = json.loads(response.text)['result']
        for data in main_data:
            actions_list.append(data['id'])
        return actions_list
    else:
        message = 'ozon_system.supplyment.get_action_list Не получил данные от метода списка акций ОЗОН api-seller.ozon.ru/v1/actions'
        bot.send_message(chat_id=CHAT_ID_ADMIN, text=message)


@sender_error_to_tg
def get_articles_data_from_database(ur_lico):
    """Получает данные артикулов из внутренней базы данных"""
    data = ArticleGroup.objects.filter(group__company=ur_lico)
    # Словарь вида {product_id: минимальная_цена}
    campaign_min_price_dict = {}
    for campaign_data in data:
        campaign_min_price_dict[campaign_data.common_article.ozon_product_id] = campaign_data.group.min_price
    return campaign_min_price_dict


@sender_error_to_tg
def get_action_data(action_id, header, action_info_list=None, offset=0, koef=0):
    """
    Получает артикулы и их цену в акции
    Возвращает словарь вида: {артикул: цена_по_акции}
    """
    if action_info_list == None:
        action_info_list = []
    action_articles_info_dict = {}
    url = 'https://api-seller.ozon.ru/v1/actions/products'
    payload = json.dumps({
        "action_id": action_id,
        "limit": 100,
        "offset": offset
    })
    response = requests.request("POST", url, headers=header, data=payload)

    if response.status_code == 200:
        main_data = json.loads(response.text)['result']['products']
        for data in main_data:
            action_info_list.append(data)
        if len(main_data) == 100:
            koef += 1
            offset = 100 * koef
            get_action_data(action_id, header, action_info_list, offset, koef)
        for action_data in action_info_list:
            action_articles_info_dict[action_data['id']
                                      ] = action_data['action_price']
        return action_articles_info_dict


@sender_error_to_tg
def get_articles_price_from_actions(header):
    """
    Получает артикулы и их цену в акции.
    Возвращает словарь вида: {id_акции: {product_id: цена_по_акции}}
    """
    actions_list = get_actions_list(header)
    main_actions_info_dict = {}

    for action in actions_list:
        articles_action_price_dict = get_action_data(action, header)
        main_actions_info_dict[action] = articles_action_price_dict
        time.sleep(2)
    return main_actions_info_dict


@sender_error_to_tg
def compare_action_articles_and_database(header, ur_lico):
    """Сравнивает артикулы из акций и из базы данных"""
    actions_data = get_articles_price_from_actions(header)

    database_data = get_articles_data_from_database(ur_lico)
    # Словарь для удаляемых артикулов ииз кампании
    del_articles = {}
    for action, action_articles in actions_data.items():
        inner_list = []
        for article, price in database_data.items():
            if article in action_articles:
                if action_articles[article] < database_data[article]:
                    inner_list.append(article)
        if inner_list:
            del_articles[action] = inner_list
    print(del_articles)
    return del_articles


@sender_error_to_tg
def del_articles_from_action(header, action_id, articles_list, ur_lico):
    """Удаляет список артикулов из акции"""
    url = 'https://api-seller.ozon.ru/v1/actions/products/deactivate'
    payload = json.dumps({
        "action_id": action_id,
        "product_ids": articles_list
    })
    response = requests.request("POST", url, headers=header, data=payload)
    if response.status_code == 200:
        text = f'{ur_lico}. Из акции {action_id} удалили артикулы: {articles_list}'
        for chat_id in admins_chat_id_list:
            bot.send_message(chat_id=chat_id,
                             text=text, parse_mode='HTML')


@sender_error_to_tg
def delete_articles_with_low_price(header, ur_lico):
    """
    Удаляет артикулы, цены которых в акциях ниже,
    чем выставленная минимальная цена
    """
    action_data = compare_action_articles_and_database(header, ur_lico)
    if action_data:
        for action_id, articles_list in action_data.items():
            del_articles_from_action(header, action_id, articles_list, ur_lico)


@sender_error_to_tg
def delete_ozon_articles_with_low_price_current_ur_lico(url_lico):
    """
    Удаляет артикулы из акций ОЗОН, если цена в акции меньше,
    чем в базе даных. Только для входящего юр. лица.
    """
    header = header_ozon_dict[url_lico]
    delete_articles_with_low_price(header, url_lico)
    text = 'Отработала функция ozon_system.tasks.delete_ozon_articles_with_low_price_from_actions'
    bot.send_message(chat_id=CHAT_ID_ADMIN,
                     text=text, parse_mode='HTML')
