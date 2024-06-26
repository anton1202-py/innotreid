import asyncio
import math
import time
from datetime import datetime, timedelta

from api_request.wb_requests import (
    advertisment_campaign_clusters_statistic, advertisment_campaign_list,
    create_auto_advertisment_campaign, get_del_minus_phrase_to_auto_campaigns,
    get_del_minus_phrase_to_catalog_search_campaigns,
    statistic_search_campaign_keywords)
from celery_tasks.celery import app
from create_reklama.minus_words_working import (
    get_campaigns_list_from_api_wb, get_common_minus_phrase,
    get_minus_phrase_from_wb_auto_campaigns,
    get_minus_phrase_from_wb_search_catalog_campaigns)
from create_reklama.models import AllMinusWords, CreatedCampaign
from django.db.models import Q
from motivation.models import Selling
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg
from reklama.models import AdvertisingCampaign, ProcentForAd, UrLico

from web_barcode.constants_file import CHAT_ID_ADMIN, bot, header_wb_dict


@app.task
def set_up_minus_phrase_to_search_catalog_campaigns():
    """Устанавливает минус фразы для кампании каталог + поиск"""
    _, catalog_search_campaigns_list = get_campaigns_list_from_api_wb()
    common_minus_phrase_list = get_common_minus_phrase()
    for main_data in catalog_search_campaigns_list:
        for ur_lico, campaign_list in main_data.items():
            header = header_wb_dict[ur_lico]
            for campaign_number in campaign_list:
                campaign_minus_phrase_list = get_minus_phrase_from_wb_search_catalog_campaigns(
                    ur_lico, campaign_number)
                for minus_word in common_minus_phrase_list:
                    if minus_word not in campaign_minus_phrase_list:
                        campaign_minus_phrase_list.append(minus_word)
                get_del_minus_phrase_to_catalog_search_campaigns(
                    header, campaign_number, campaign_minus_phrase_list)


@app.task
def set_up_minus_phrase_to_auto_campaigns():
    """Устанавливает минус фразы для автоматческих кампаний"""
    auto_campaigns_list, _ = get_campaigns_list_from_api_wb()
    common_minus_phrase_list = get_common_minus_phrase()
    for main_data in auto_campaigns_list:
        for ur_lico, campaign_list in main_data.items():
            header = header_wb_dict[ur_lico]
            for campaign_number in campaign_list:
                campaign_minus_phrase_list = get_minus_phrase_from_wb_auto_campaigns(
                    ur_lico, campaign_number)

                for minus_word in common_minus_phrase_list:
                    if minus_word not in campaign_minus_phrase_list:
                        campaign_minus_phrase_list.append(minus_word)
                get_del_minus_phrase_to_auto_campaigns(
                    header, campaign_number, campaign_minus_phrase_list)
