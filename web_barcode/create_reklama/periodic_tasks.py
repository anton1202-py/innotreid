import asyncio
import math
import time
from datetime import datetime, timedelta

from api_request.wb_requests import (
    advertisment_campaign_clusters_statistic, advertisment_campaign_list,
    create_auto_advertisment_campaign, get_del_minus_phrase_to_auto_campaigns,
    get_del_minus_phrase_to_catalog_search_campaigns, get_front_api_wb_info)
from celery_tasks.celery import app
from create_reklama.add_balance import (ad_list, count_sum_orders,
                                        header_determinant,
                                        replenish_campaign_budget,
                                        send_common_message,
                                        start_add_campaign,
                                        wb_ooo_fbo_stock_data)
from create_reklama.minus_words_working import (
    get_campaigns_list_from_api_wb, get_common_minus_phrase,
    get_minus_phrase_from_wb_auto_campaigns,
    get_minus_phrase_from_wb_search_catalog_campaigns)
from create_reklama.models import AllMinusWords, CreatedCampaign
from create_reklama.supplyment import (filter_campaigns_status_type,
                                       update_campaign_budget,
                                       update_campaign_cpm)
from django.db.models import Q
from motivation.models import Selling
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg
from reklama.models import (AdvertisingCampaign, DataOooWbArticle,
                            ProcentForAd, UrLico)
from reklama.supplyment import ozon_adv_campaign_articles_name_data

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
    ur_lico_data = UrLico.objects.all()
    for ur_lico_obj in ur_lico_data:
        campaign_data = CreatedCampaign.objects.filter(
            ur_lico=ur_lico_obj, campaign_type=8)
        message = str(campaign_data)[:4000]
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message)

        common_minus_phrase_list = get_common_minus_phrase(ur_lico_obj)
        message = str('common_minus_phrase_list',
                      common_minus_phrase_list)[:4000]
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message)
        if campaign_data:
            for data in campaign_data:
                header = header_wb_dict[ur_lico_obj.ur_lice_name]
                campaign_minus_phrase_list = get_minus_phrase_from_wb_auto_campaigns(
                    ur_lico_obj.ur_lice_name, data.campaign_number)
                message = str(campaign_minus_phrase_list,
                              data.campaign_number, data.campaign_name)[:4000]
                bot.send_message(chat_id=CHAT_ID_ADMIN,
                                 text=message)
                if common_minus_phrase_list:
                    for minus_word in common_minus_phrase_list:
                        if minus_word not in campaign_minus_phrase_list:
                            campaign_minus_phrase_list.append(minus_word)
                    get_del_minus_phrase_to_auto_campaigns(
                        header, data.campaign_number, campaign_minus_phrase_list)


@app.task
def update_articles_price_info_in_campaigns():
    """Обновляет информацию по цене артикулов в кампаниях"""
    ur_lico_data = UrLico.objects.all()

    for ur_lico_obj in ur_lico_data:
        campaigns_data = CreatedCampaign.objects.filter(ur_lico=ur_lico_obj)
        for article in campaigns_data:
            common_info = get_front_api_wb_info(article.articles_name)
            if common_info:
                price = ''
                if common_info['data']['products']:
                    price = int(common_info['data']['products'][0]
                                ['salePriceU'])//100

                article.article_price_on_page = price
                article.save()


@app.task
def update_campaign_status():
    """Обновляет статус кампаний"""
    ur_lico_data = UrLico.objects.all()
    answer_data = filter_campaigns_status_type()
    for ur_lico_obj in ur_lico_data:
        answer_campaigns_info = answer_data[ur_lico_obj.ur_lice_name]
        for campaign_type, data in answer_campaigns_info.items():
            campaigns_data = CreatedCampaign.objects.filter(
                ur_lico=ur_lico_obj, campaign_type=campaign_type
            )
            if campaigns_data.exists():
                for campaign_status, campaign_list in data.items():
                    for campaign_obj in campaigns_data:
                        if int(campaign_obj.campaign_number) in campaign_list and campaign_status != 7:
                            campaign_obj.campaign_status = campaign_status
                            campaign_obj.save()
                        elif int(campaign_obj.campaign_number) in campaign_list and campaign_status == 7:
                            campaign_obj.delete()
    campaigns_data = CreatedCampaign.objects.filter(
        campaign_status=7
    )
    for i in campaigns_data:
        i.delete()


@app.task
def update_campaign_budget_and_cpm():
    """
    Обновляет данные кампании (баланс и cpm)
    """
    ur_lico_data = UrLico.objects.all()

    for ur_lico_obj in ur_lico_data:
        campaigns_list = []
        header = header_wb_dict[ur_lico_obj.ur_lice_name]
        campaign_queryset = CreatedCampaign.objects.filter(ur_lico=ur_lico_obj)
        for campaign_obj in campaign_queryset:
            update_campaign_budget(campaign_obj, header)
            campaigns_list.append(int(campaign_obj.campaign_number))

        check_number = math.ceil(len(campaigns_list)/50)

        for i in range(check_number):
            start_point = i*50
            finish_point = (i+1)*50
            data_adv_list = campaigns_list[
                start_point:finish_point]
            update_campaign_cpm(data_adv_list, ur_lico_obj, header)


@app.task
def budget_working():
    """Пополняет бюджет рекламных кампаний WB"""
    messages_list = []
    campaign_data_dict = count_sum_orders()
    if campaign_data_dict:
        for ur_lico, campaign_data in campaign_data_dict.items():
            for campaign, budget in campaign_data.items():
                header = header_wb_dict[ur_lico]
                campaign_obj = CreatedCampaign.objects.get(
                    ur_lico__ur_lice_name=ur_lico, campaign_number=campaign)
                message = replenish_campaign_budget(
                    campaign, budget, header, campaign_obj)
                messages_list.append(message)
                time.sleep(3)
                start_add_campaign(campaign, header)
    send_common_message(messages_list)


# ========== СОПОСТАВЛЯЕТ КАКОЙ АРТИКУЛ В КАКОЙ РЕКЛАМНОЙ КАМПАНИИ НАХОДИТСЯ ========= #
@sender_error_to_tg
@app.task
def matching_wb_ooo_article_campaign():
    """WILDBERRIES. Сверяет артикулы ООО с кампаниями ВБ"""
    DataOooWbArticle.objects.all().update(ad_campaign=None)
    DataOooWbArticle.objects.all().update(wb_campaigns_name=None)
    campaigns_data = CreatedCampaign.objects.filter(
        ur_lico__ur_lice_name='ООО Иннотрейд')
    for campaign in campaigns_data:
        article = ''
        article_list = campaign.articles_name
        wb_campaign_name = campaign.campaign_name
        if type(article_list) == list:
            article = article_list[0]
        else:
            article = article_list
            if Articles.objects.filter(wb_nomenclature=article).exists():
                article_obj = Articles.objects.filter(
                    wb_nomenclature=article)[0]
                if not DataOooWbArticle.objects.filter(
                        wb_article=article_obj).exists():
                    DataOooWbArticle(wb_article=article_obj).save()
                matching_data = DataOooWbArticle.objects.get(
                    wb_article=article_obj)
                if matching_data.ad_campaign:
                    if str(campaign.campaign_number) not in str(matching_data.ad_campaign):
                        matching_data.ad_campaign = str(
                            matching_data.ad_campaign) + ', ' + str(campaign.campaign_number)
                else:
                    matching_data.ad_campaign = campaign.campaign_number
                if matching_data.wb_campaigns_name:
                    if str(wb_campaign_name) not in str(matching_data.wb_campaigns_name):
                        matching_data.wb_campaigns_name = str(
                            matching_data.wb_campaigns_name) + ', ' + str(wb_campaign_name)
                else:
                    matching_data.wb_campaigns_name = wb_campaign_name
                matching_data.save()
        time.sleep(3)


@app.task
def matching_ozon_ooo_article_campaign():
    """OZON. Сверяет артикулы ООО с кампаниями OZON"""
    main_campaigns_data = ozon_adv_campaign_articles_name_data('ООО Иннотрейд')
    DataOooWbArticle.objects.all().update(ozon_ad_campaign=None)
    DataOooWbArticle.objects.all().update(ozon_campaigns_name=None)
    for campaign, campaigns_data in main_campaigns_data.items():
        if campaigns_data['Артикулы']:

            for article in campaigns_data['Артикулы']:
                article_obj = ''
                if Articles.objects.filter(ozon_product_id=int(article)).exists():
                    article_obj = Articles.objects.filter(
                        ozon_product_id=article)[0]
                elif Articles.objects.filter(ozon_sku=int(article)).exists():
                    article_obj = Articles.objects.filter(
                        ozon_sku=article)[0]
                elif Articles.objects.filter(ozon_fbo_sku_id=int(article)).exists():
                    article_obj = Articles.objects.filter(
                        ozon_fbo_sku_id=article)[0]
                elif Articles.objects.filter(ozon_fbs_sku_id=int(article)).exists():
                    article_obj = Articles.objects.filter(
                        ozon_fbs_sku_id=article)[0]
                if article_obj:
                    matching_data = DataOooWbArticle.objects.filter(
                        wb_article=article_obj)[0]
                    if matching_data.ozon_ad_campaign:
                        if str(campaign) not in str(matching_data.ozon_ad_campaign):
                            matching_data.ozon_ad_campaign = str(
                                matching_data.ozon_ad_campaign) + ', ' + str(campaign)
                    else:
                        matching_data.ozon_ad_campaign = campaign
                    if matching_data.ozon_campaigns_name:
                        if str(campaigns_data['Название']) not in str(matching_data.ozon_campaigns_name):
                            matching_data.ozon_campaigns_name = str(
                                matching_data.ozon_campaigns_name) + ', ' + str(campaigns_data['Название'])
                    else:
                        matching_data.ozon_campaigns_name = campaigns_data['Название']
                    matching_data.save()


@sender_error_to_tg
@app.task
def wb_ooo_fbo_stock_count():
    """WILDBERRIES. Смотрит и записывает остаток FBO на ВБ каждого артикула"""
    main_data = wb_ooo_fbo_stock_data()
    for all_data in main_data:
        for data in all_data:
            if Articles.objects.filter(
                    wb_nomenclature=data['nmID']).exists():
                article_obj = Articles.objects.filter(
                    wb_nomenclature=data['nmID'])[0]
                matching_data = DataOooWbArticle.objects.get(
                    wb_article=article_obj)
                matching_data.fbo_amount = data['stocks']['stocksWb']
                matching_data.save()

# ========== КОНЕЦ СОПОСТАВЛЯЕТ КАКОЙ АРТИКУЛ В КАКОЙ РЕКЛАМНОЙ КАМПАНИИ НАХОДИТСЯ ========= #
