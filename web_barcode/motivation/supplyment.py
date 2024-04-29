import json
import math
import os
import time
from datetime import datetime, timedelta

import requests
import telegram
from django.contrib.auth.models import User
# from celery_tasks.celery import app
from dotenv import load_dotenv
from motivation.models import DesignUser, Lighters
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg
from reklama.models import (AdvertisingCampaign, CompanyStatistic,
                            DataOooWbArticle, OooWbArticle, OzonCampaign,
                            ProcentForAd, SalesArticleStatistic,
                            WbArticleCommon, WbArticleCompany)

from web_barcode.constants_file import (CHAT_ID_ADMIN, TELEGRAM_TOKEN,
                                        header_ozon_dict, header_wb_data_dict,
                                        header_wb_dict, header_yandex_dict,
                                        ozon_adv_client_access_id_dict,
                                        ozon_adv_client_secret_dict,
                                        ozon_api_token_dict,
                                        wb_headers_karavaev, wb_headers_ooo,
                                        yandex_business_id_dict)


def articles_data_merge():
    main_data = Articles.objects.all()
    for data in main_data:
        s = data.common_article
        if not s[0].isdigit() and s[0] not in ['d', 'D', ' ']:
            Lighters(
                article=data
            ).save()
    print(len(main_data))


def designer_data_merge():
    main_data = User.objects.all()
    for data in main_data:
        print(data)
        DesignUser(
            designer=data
        ).save()
    print(len(main_data))
