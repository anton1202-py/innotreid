import math
import time
from datetime import datetime, timedelta

import pandas as pd

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
from price_system.supplyment import sender_error_to_tg, wilberries_price_change
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


def create_data_with_article_conditions(action_obj, user_chat_id):
    """Находим соответствующие акции Озон для Акции ВБ"""
    main_articles_data = ArticleMayBeInAction.objects.filter(action__marketplace__marketpalce='Wildberries', action=action_obj)
    possible_ozon_articles = {}
    articles_without_price_group = []
    for data in main_articles_data:
        article = data.article
        wb_price = data.action_price
        try:
            wb_discount = article.articlegroup.get(common_article=article).group.wb_discount/100
            wb_price_after_seller_discount = (1- wb_discount) * article.articlegroup.get(common_article=article).group.old_price
            if (wb_price_after_seller_discount - wb_price)/wb_price_after_seller_discount < 0.07:
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
        except:
            articles_without_price_group.append(article.common_article)
    if articles_without_price_group:
        message = f'Добавьте артикулам {articles_without_price_group} ценовую группу. Не могу рассчитать по ним условия участия в акции'
        bot.send_message(chat_id=user_chat_id, text=message)


    for wb_act_article, ozon_act_article in possible_ozon_articles.items():
        if not ArticleInActionWithCondition.objects.filter(
            article=wb_act_article.article,
            wb_action=wb_act_article.action,
            ozon_action_id=ozon_act_article.action,
            ).exists:
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


def wb_auto_action_article_price_excel_import(xlsx_file, ur_lico, action_obj):
    """Импортирует данные о ценах артикула в акции из Excel"""
    excel_data_common = pd.read_excel(xlsx_file)
    column_list = excel_data_common.columns.tolist()
    if 'Артикул поставщика' in column_list and 'Плановая цена для акции' in column_list and 'Загружаемая скидка для участия в акции' in column_list:
        excel_data = pd.DataFrame(excel_data_common, columns=[
                                  'Артикул поставщика', 'Артикул WB', 'Плановая цена для акции',
                                  'Текущая розничная цена', 'Текущая скидка на сайте, %'])
        wb_article_list = excel_data['Артикул WB'].to_list()
        action_price_list = excel_data['Плановая цена для акции'].to_list()
        current_price_without_discount_list = excel_data['Текущая розничная цена'].to_list()
        current_discount_list = excel_data['Текущая скидка на сайте, %'].to_list()
        for i, article in enumerate(wb_article_list):
            if Articles.objects.filter(
                    company=ur_lico, wb_nomenclature=article).exists():
                article_obj = Articles.objects.get(
                    company=ur_lico, wb_nomenclature=article)
                action_price = action_price_list[i]

                current_seller_price = current_price_without_discount_list[i] * (1 - current_discount_list[i] / 100)
                action_discount = (current_seller_price - action_price) / current_seller_price * 100
                search_params = {'action': action_obj, 'article': article_obj}
                defaults = {'action_price': action_price, 'action_discount': action_discount}
                ArticleMayBeInAction.objects.update_or_create(
                    defaults=defaults, **search_params
                ) 
    else:
        return f'Вы пытались загрузить ошибочный файл {xlsx_file}.'
    

def sender_message_about_articles_in_action_already(user_chat_id, common_message):
    """
    Отправляет сообщение пользователю в ТГ, 
    который нажал на кнопку ДОБАВИТЬ В АКЦИЮ
    Если артикулы уже находятся в этой акции
    """
    # if common_message['wb']:
        
    # message = f'Добавил в акцию ВБ {wb_action_name}: {len(wb_articles_list)} артикулов'
    # bot.send_message(chat_id=user_chat_id, text=message)


def del_articles_from_wb_action(article_obj_list, user_chat_id):
    """
    Удаляем артикулы из акции ВБ. 
    Для этого приводим цены к первоначальным значениям.
    В нашей базе ставим дату завершения участия в акции.

    Присутствуют переменные:
        price_group_info_dict = {
            group_obj: {
                wb_price: старая_цена_в_группе, 
                wb_discount: скидка_продавца,
                article_list_from_group: список_актикулов_из_этой_группы
            }
        }

    """
    price_group_info_dict ={}
    for article_obj in article_obj_list:
        if article_obj.articlegroup.filter(common_article=article_obj).exists():
            price_group = article_obj.articlegroup.get(common_article=article_obj).group
            group_price = article_obj.articlegroup.get(common_article=article_obj).group.old_price
            group_discount = article_obj.articlegroup.get(common_article=article_obj).group.wb_discount
    
            if price_group not in price_group_info_dict:
                price_group_info_dict[price_group] = {
                    'wb_price': group_price, 
                    'wb_discount': group_discount,
                    'article_list_from_group': [article_obj.wb_nomenclature]
                }
            else:
                price_group_info_dict[price_group]['article_list_from_group'].append(article_obj.wb_nomenclature)
        else:
            message = f'У артикула {article_obj.common_article} не нашел ценовую группу. Не могу убрать его из акции ВБ'
            bot.send_message(chat_id=user_chat_id, text=message)

    # Вызываю функцию изменения цен у артикулов:
    for group, info in price_group_info_dict.items():
        ur_lico = group.company
        try:
            wilberries_price_change(ur_lico, info['article_list_from_group'], info['wb_price'], info['wb_discount'])
        except Exception as e:
            message = f'Не удалось вывести из акции ВБ артикулы: {str(info["article_list_from_group"])[:2000]}. Произовшла ошибка: {e}'
            bot.send_message(chat_id=user_chat_id, text=message[:4000])


def del_articles_from_ozon_action(article_obj_list, user_chat_id):
    """
    Удаляем артикулы из акций ОЗОН. 
    """
    price_group_info_dict ={}
    for article_obj in article_obj_list:
        if article_obj.articlegroup.filter(common_article=article_obj).exists():
            price_group = article_obj.articlegroup.get(common_article=article_obj).group
            group_price = article_obj.articlegroup.get(common_article=article_obj).group.old_price
            group_discount = article_obj.articlegroup.get(common_article=article_obj).group.wb_discount
    
            if price_group not in price_group_info_dict:
                price_group_info_dict[price_group] = {
                    'wb_price': group_price, 
                    'wb_discount': group_discount,
                    'article_list_from_group': [article_obj.wb_nomenclature]
                }
            else:
                price_group_info_dict[price_group]['article_list_from_group'].append(article_obj.wb_nomenclature)
        else:
            message = f'У артикула {article_obj.common_article} не нашел ценовую группу. Не могу убрать его из акции ВБ'
            bot.send_message(chat_id=user_chat_id, text=message)

    # Вызываю функцию изменения цен у артикулов:
    for group, info in price_group_info_dict.items():
        ur_lico = group.company
        try:
            wilberries_price_change(ur_lico, info['article_list_from_group'], info['wb_price'], info['wb_discount'])
        except Exception as e:
            message = f'Не удалось вывести из акции ВБ артикулы: {str(info["article_list_from_group"])[:2000]}. Произовшла ошибка: {e}'
            bot.send_message(chat_id=user_chat_id, text=message[:4000])