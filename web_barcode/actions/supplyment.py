import math
import time
from datetime import datetime, timedelta

from api_request.wb_requests import (
    advertisment_campaign_clusters_statistic, advertisment_campaign_list,
    create_auto_advertisment_campaign, get_del_minus_phrase_to_auto_campaigns,
    get_del_minus_phrase_to_catalog_search_campaigns, get_front_api_wb_info,
    replenish_deposit_campaigns, start_advertisment_campaigns, wb_action_details_info, wb_actions_first_list, wb_articles_in_action)
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
from create_reklama.models import (AllMinusWords, AutoReplenish,
                                   CreatedCampaign, ReplenishWbCampaign,
                                   StartPausaCampaign)
from create_reklama.supplyment import (filter_campaigns_status_only,
                                       filter_campaigns_status_type,
                                       update_campaign_budget,
                                       update_campaign_cpm, white_list_phrase)
from django.db.models import Q
from motivation.models import Selling
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg
from reklama.models import DataOooWbArticle, UrLico
from reklama.supplyment import ozon_adv_campaign_articles_name_data

from actions.models import Action, ArticleInAction, ArticleInActionWithCondition, ArticleMayBeInAction
from web_barcode.constants_file import (CHAT_ID_ADMIN, bot,
                                        actions_info_users_list,
                                        header_wb_dict)
from database.models import CodingMarketplaces



def add_article_may_be_in_action(ur_lico_obj, article_action_data, action_obj):
    """Описывает артикулы, которые могут быть в акции"""
    if article_action_data:
        for_create_list = []
        for data in article_action_data['data']['nomenclatures']:
            if Articles.objects.filter(company=ur_lico_obj.ur_lice_name, wb_nomenclature=data['id']).exists():
                article_obj = Articles.objects.get(company=ur_lico_obj.ur_lice_name, wb_nomenclature=data['id'])
                maybe_obj = ArticleMayBeInAction(
                    action=action_obj,
                    article=article_obj,
                    action_price=data['planPrice'],
                    action_discount=data['planDiscount']
                )
                for_create_list.append(maybe_obj)
        if for_create_list:
            ArticleMayBeInAction.objects.bulk_create(for_create_list)


def create_data_with_article_conditions():
    """Находим соответствующие акции Озон для Акции ВБ"""
    main_articles_data = ArticleMayBeInAction.objects.filter(action__marketplace__marketpalce='Wildberries', action__date_finish__gt=datetime.now())
    possible_ozon_articles = {}
    for data in main_articles_data:
        article = data.article
        wb_price = data.action_price
        ozon_variant = ArticleMayBeInAction.objects.filter(action__marketplace__marketpalce='Ozon', action__date_finish__gt=datetime.now(), article=article)
        ozon_art = ''
        ozon_price = 10**6
        for ozon_article in ozon_variant:
            if ozon_article.action_price > wb_price:
                differ = (ozon_article.action_price - wb_price) / wb_price * 100
                if differ < 4:
                    if ozon_article.action_price < ozon_price:
                        ozon_price = ozon_article.action_price
                        ozon_art = ozon_article
            
        if ozon_art:
            possible_ozon_articles[data] = ozon_art

    for wb_act_article, ozon_act_article in possible_ozon_articles.items():
        ArticleInActionWithCondition(
            article=wb_act_article.article,
            wb_action=wb_act_article.action,
            ozon_action_id=ozon_act_article.action,
        ).save()


def save_articles_added_to_action(article_obj_list, action_obj):
    """Добавляет данные в БД об артикулах, которые попали в акцию"""
    existing_articles_in_action = {}
    existing_articles_list = []
    for article_obj in article_obj_list:
        if not ArticleInAction.objects.filter(
            article=article_obj,
            action=action_obj).exists():
            ArticleInAction(
                article=article_obj,
                action=action_obj,
                date_start=datetime.now()
            ).save()
        else:
            existing_articles_list.append(article_obj)
    if existing_articles_list:
        existing_articles_in_action[action_obj] = existing_articles_list
        return existing_articles_in_action

def sender_message_about_articles_in_action_already(user_chat_id, common_message):
    """
    Отправляет сообщение пользователю в ТГ, 
    который нажал на кнопку ДОБАВИТЬ В АКЦИЮ
    Если артикулы уже находятся в этой акции
    """
    # if common_message['wb']:
        
    # message = f'Добавил в акцию ВБ {wb_action_name}: {len(wb_articles_list)} артикулов'
    # bot.send_message(chat_id=user_chat_id, text=message)