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

from actions.models import Action, ArticleMayBeInAction
from web_barcode.constants_file import (CHAT_ID_ADMIN, bot,
                                        actions_info_users_list,
                                        header_wb_dict)
from database.models import CodingMarketplaces



def add_article_may_be_in_action(ur_lico_obj, header, action_number):
    """Описывает артикулы, которые могут быть в акции"""

    article_action_data = wb_articles_in_action(header, action_number)
    action_obj = Action.objects.get(ur_lico=ur_lico_obj, action_number=action_number)
    if article_action_data:
        for_create_list = []
        print('len(article_action_data', len(article_action_data['data']['nomenclatures']))
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