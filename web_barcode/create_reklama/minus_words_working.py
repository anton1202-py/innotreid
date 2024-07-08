import asyncio
import math
import time
from datetime import datetime, timedelta

from api_request.wb_requests import (
    advertisment_campaign_clusters_statistic, advertisment_campaign_list,
    create_auto_advertisment_campaign, get_del_minus_phrase_to_auto_campaigns,
    get_del_minus_phrase_to_catalog_search_campaigns,
    statistic_search_campaign_keywords)
from create_reklama.models import AllMinusWords
from price_system.supplyment import sender_error_to_tg
from reklama.models import UrLico

from web_barcode.constants_file import CHAT_ID_ADMIN, header_wb_dict


@sender_error_to_tg
def get_campaigns_list_from_api_wb():
    """
    Получает списки рекламных кампаний с АПИ ВБ,
    статус которых:
    4 - готова к запуску
    9 - идут показы
    11 - на паузе

    Описание типов кампании:
    4 - в каталоге
    5 - в карточке товара
    6 - в поиске
    7 - в рекомендациях на главной странице
    8 - автоматическая
    9 - поиск + каталог
    """
    ur_lico_main = UrLico.objects.all()
    catalog_search_campaigns_list = []
    auto_campaigns_list = []

    accept_status_list = [4, 9, 11]
    for ur_lico_obj in ur_lico_main:
        header = header_wb_dict[ur_lico_obj.ur_lice_name]
        campaign_main_data = advertisment_campaign_list(header)['adverts']
        inner_catalog_search_list = []
        inner_auto_list = []
        for data in campaign_main_data:
            if data['status'] in accept_status_list:
                if data['type'] == 9:
                    for campaign in data['advert_list']:
                        inner_catalog_search_list.append(campaign['advertId'])
                elif data['type'] == 8:
                    for campaign in data['advert_list']:
                        inner_auto_list.append(campaign['advertId'])
        auto_campaigns_list.append({ur_lico_obj.ur_lice_name: inner_auto_list})
        catalog_search_campaigns_list.append(
            {ur_lico_obj.ur_lice_name: inner_catalog_search_list})

    return auto_campaigns_list, catalog_search_campaigns_list


@sender_error_to_tg
def get_common_minus_phrase(ur_lico_obj):
    """
    Получает общие минус фразы из базы данных.
    Возвращает список общих минус фраз
    """
    common_data = AllMinusWords.objects.filter(ur_lico=ur_lico_obj)
    minus_phrase_list = []
    if common_data:
        for word_obj in common_data:
            minus_phrase_list.append(word_obj.word)
        return minus_phrase_list
    else:
        return []


@sender_error_to_tg
def get_minus_phrase_from_wb_search_catalog_campaigns(ur_lico, campaign_number):
    """Получает минус слова из кампаний каталог + поиск из ВБ"""
    header = header_wb_dict[ur_lico]
    campaigns_data = statistic_search_campaign_keywords(
        header, campaign_number)
    minus_phrase_list = campaigns_data['words']['phrase']
    return minus_phrase_list


@sender_error_to_tg
def get_minus_phrase_from_wb_auto_campaigns(ur_lico, campaign_number):
    """Получает минус слова из автоматической кампании"""
    header = header_wb_dict[ur_lico]
    campaigns_data = advertisment_campaign_clusters_statistic(
        header, campaign_number)
    minus_phrase_list = campaigns_data['excluded']
    return minus_phrase_list
