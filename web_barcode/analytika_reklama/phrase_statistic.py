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
