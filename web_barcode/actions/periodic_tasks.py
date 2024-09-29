import math
import time
from datetime import datetime, timedelta

from api_request.wb_requests import (
    advertisment_campaign_clusters_statistic, advertisment_campaign_list,
    create_auto_advertisment_campaign, get_del_minus_phrase_to_auto_campaigns,
    get_del_minus_phrase_to_catalog_search_campaigns, get_front_api_wb_info,
    replenish_deposit_campaigns, start_advertisment_campaigns, wb_action_details_info, wb_actions_first_list)
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

from actions.models import Action
from actions.supplyment import add_article_may_be_in_action
from web_barcode.constants_file import (CHAT_ID_ADMIN, bot,
                                        actions_info_users_list,
                                        header_wb_dict)
from database.models import CodingMarketplaces


def add_new_actions_wb_to_db():
    """Добавляет новую акцию ВБ в базу данных"""

    new_action_list = []
    for ur_lico_obj in UrLico.objects.all():
        header  = header_wb_dict[ur_lico_obj.ur_lice_name]
        actions_data = wb_actions_first_list(header)
        actions_not_exist_str = ''
        if actions_data:
            actions_info = actions_data['data']['promotions']
            for action in actions_info:
                add_article_may_be_in_action(ur_lico_obj, header, action['id'])
                if not Action.objects.filter(ur_lico=ur_lico_obj, action_number=action['id']).exists():
                    message = (f"У Юр. лица {ur_lico_obj.ur_lice_name} появилась новая акция: "
                                f"{action['id']}: {action['name']}.\n"
                                f"Дата начала: {datetime.strptime(action['startDateTime'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')}.\n"
                                f"Дата завершения {datetime.strptime(action['endDateTime'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')}.")
                    for chat_id in actions_info_users_list:
                        bot.send_message(chat_id=chat_id,
                             text=message)
                    actions_not_exist_str += f"promotionIDs={action['id']}&"
        if actions_not_exist_str:
            actions_details = wb_action_details_info(header, actions_not_exist_str)
            if actions_details and 'data' in actions_details:
                for detail in actions_details['data']['promotions']:
                    action_obj = Action(
                        ur_lico=ur_lico_obj,
                        marketplace=CodingMarketplaces.objects.get(marketpalce='Wildberries'),
                        action_number = detail['id'],
                        name = detail['name'],
                        description = detail['description'],
                        date_start = detail['startDateTime'],
                        date_finish = detail['endDateTime'],
                        action_type = detail['type'],
                        articles_amount = detail['inPromoActionTotal'],
                    )
                    new_action_list.append(action_obj)

    if new_action_list:
        Action.objects.bulk_create(new_action_list)
                    