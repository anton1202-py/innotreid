import math
import time
from datetime import datetime, timedelta

from analytika_reklama.models import (CommonCampaignDescription,
                                      DailyCampaignParameters, KeywordPhrase,
                                      StatisticCampaignKeywordPhrase)
from api_request.wb_requests import (advertisment_campaign_clusters_statistic,
                                     advertisment_campaign_list,
                                     advertisment_campaigns_list_info,
                                     advertisment_statistic_info,
                                     statistic_keywords_auto_campaign)
from create_reklama.models import CreatedCampaign
from django.db.models import Q
from motivation.models import Selling
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg
from reklama.models import UrLico

from web_barcode.constants_file import (CHAT_ID_ADMIN,
                                        WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
                                        WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
                                        bot, header_wb_dict)


def get_auto_campaign_statistic_common_data():
    """Получает статистику каждой РК из внутренней баз данных"""
    common_data = CreatedCampaign.objects.all()

    for campaign_obj in common_data:
        header = header_wb_dict[campaign_obj.ur_lico.ur_lice_name]

        campaign_statistic = statistic_keywords_auto_campaign(
            header, int(campaign_obj.campaign_number))

        for data in campaign_statistic:
            date_str = data['date']
            date_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z')
            date = date_obj - timedelta(days=1)
            today_date = datetime.now(date_obj.tzinfo).replace(
                hour=0, minute=0, second=0, microsecond=0)

            if date.date() < today_date.date():
                phrase_stat = data['stat']
                for phrase_data in phrase_stat:
                    phrase = phrase_data['keyword']
                    views = phrase_data['views']
                    clicks = phrase_data['clicks']
                    ctr = phrase_data['ctr']
                    summ = phrase_data['sum']

                    phrase_obj = add_keyphrase_to_db(phrase)
                    if not StatisticCampaignKeywordPhrase.objects.filter(statistic_date=date_str,
                                                                         keyword=phrase_obj,
                                                                         campaign=campaign_obj).exists():
                        StatisticCampaignKeywordPhrase(
                            statistic_date=date_str,
                            keyword=phrase_obj,
                            campaign=campaign_obj,
                            views=views,
                            clicks=clicks,
                            ctr=ctr,
                            summ=summ
                        ).save()


def add_keyphrase_to_db(phrase: str):
    """
    Записывает ключевую фразу в базу данных и возвращает ее объект
    А если есть - возвращает ее объект
    """

    phrase_obj, created = KeywordPhrase.objects.get_or_create(phrase=phrase)

    if created:
        return phrase_obj
    else:
        return phrase_obj
