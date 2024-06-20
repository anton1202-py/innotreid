import json
import math
import os
import time
from datetime import datetime, timedelta

import requests
import telegram
from analytika_reklama.models import DailyCampaignParameters
from celery_tasks.celery import app
from dotenv import load_dotenv
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg
from reklama.models import (AdvertisingCampaign, CompanyStatistic,
                            DataOooWbArticle, OooWbArticle, OzonCampaign,
                            ProcentForAd, SalesArticleStatistic,
                            WbArticleCommon, WbArticleCompany)
from reklama.supplyment import (ad_list, count_sum_orders, header_determinant,
                                ooo_wb_articles_info,
                                ozon_adv_campaign_articles_name_data,
                                replenish_campaign_budget, send_common_message,
                                start_add_campaign, wb_articles_in_campaign,
                                wb_articles_in_campaign_and_name,
                                wb_ooo_fbo_stock_data)

# Загрузка переменных окружения из файла .env
dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)


REFRESH_TOKEN_DB = os.getenv('REFRESH_TOKEN_DB')
APP_KEY_DB = os.getenv('APP_KEY_DB')
APP_SECRET_DB = os.getenv('APP_SECRET_DB')

API_KEY_WB_IP = os.getenv('API_KEY_WB_IP')
YANDEX_IP_KEY = os.getenv('YANDEX_IP_KEY')

OZON_IP_API_TOKEN = os.getenv('OZON_IP__API_TOKEN')
API_KEY_OZON_KARAVAEV = os.getenv('API_KEY_OZON_KARAVAEV')
CLIENT_ID_OZON_KARAVAEV = os.getenv('CLIENT_ID_OZON_KARAVAEV')

OZON_OOO_API_TOKEN = os.getenv('OZON_OOO_API_TOKEN')
OZON_OOO_CLIENT_ID = os.getenv('OZON_OOO_CLIENT_ID')

OZON_IP_ADV_CLIENT_ACCESS_ID = os.getenv('OZON_IP_ADV_CLIENT_ACCESS_ID')
OZON_IP_ADV_CLIENT_SECRET = os.getenv('OZON_IP_ADV_CLIENT_SECRET')

OZON_OOO_ADV_CLIENT_ACCESS_ID = os.getenv('OZON_OOO_ADV_CLIENT_ACCESS_ID')
OZON_OOO_ADV_CLIENT_SECRET = os.getenv('OZON_OOO_ADV_CLIENT_SECRET')

YANDEX_OOO_KEY = os.getenv('YANDEX_OOO_KEY')
WB_OOO_API_KEY = os.getenv('WB_OOO_API_KEY')


TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID_ADMIN = os.getenv('CHAT_ID_ADMIN')
CHAT_ID_MANAGER = os.getenv('CHAT_ID_MANAGER')
CHAT_ID_EU = os.getenv('CHAT_ID_EU')
CHAT_ID_AN = os.getenv('CHAT_ID_AN')

campaign_budget_users_list = [CHAT_ID_ADMIN, CHAT_ID_EU]

bot = telegram.Bot(token=TELEGRAM_TOKEN)

wb_headers_karavaev = {
    'Content-Type': 'application/json',
    'Authorization': API_KEY_WB_IP
}
wb_headers_ooo = {
    'Content-Type': 'application/json',
    'Authorization': WB_OOO_API_KEY
}

ozon_headers_karavaev = {
    'Api-Key': OZON_IP_API_TOKEN,
    'Content-Type': 'application/json',
    'Client-Id': CLIENT_ID_OZON_KARAVAEV
}
ozon_headers_ooo = {
    'Api-Key': OZON_OOO_API_TOKEN,
    'Content-Type': 'application/json',
    'Client-Id': OZON_OOO_CLIENT_ID
}

payload_ozon_adv_ooo = json.dumps({
    'client_id': OZON_OOO_ADV_CLIENT_ACCESS_ID,
    'client_secret': OZON_OOO_ADV_CLIENT_SECRET,
    "grant_type": "client_credentials"
})
payload_ozon_adv_ip = json.dumps({
    'client_id': OZON_IP_ADV_CLIENT_ACCESS_ID,
    'client_secret': OZON_IP_ADV_CLIENT_SECRET,
    'grant_type': 'client_credentials'
})

yandex_headers_karavaev = {
    'Authorization': YANDEX_IP_KEY,
}
yandex_headers_ooo = {
    'Authorization': YANDEX_OOO_KEY,
}

wb_header = {
    'ООО Иннотрейд': wb_headers_ooo,
    'ИП Караваев': wb_headers_karavaev
}

ozon_header = {
    'ООО Иннотрейд': ozon_headers_ooo,
    'ИП Караваев': ozon_headers_karavaev
}
ozon_payload = {
    'ООО Иннотрейд': payload_ozon_adv_ooo,
    'ИП Караваев': payload_ozon_adv_ip
}

# =========== БЛОК РАБОТЫ С КАМПАНИЯМИ WILDBERRIES ========== #


@sender_error_to_tg
@app.task
def budget_working():
    """Работа с бюджетом компании"""
    messages_list = []
    campaign_data = count_sum_orders()
    print('budget_working campaign_data', campaign_data)
    if campaign_data:
        for campaign, budget in campaign_data.items():
            header = header_determinant(campaign)
            message = replenish_campaign_budget(campaign, budget, header)
            messages_list.append(message)
            time.sleep(3)
            start_add_campaign(campaign, header)
    send_common_message(messages_list)


@sender_error_to_tg
@app.task
def ooo_wb_articles_data():
    """Записывает артикулы ООО ВБ в базу данных"""
    data = ooo_wb_articles_info()
    for entry in data:
        wb_article, wb_nomenclature, article_title = entry
        if not OooWbArticle.objects.filter(wb_article=wb_article).exists():
            OooWbArticle.objects.get_or_create(
                wb_article=wb_article,
                wb_nomenclature=wb_nomenclature,
                article_title=article_title)


@sender_error_to_tg
@app.task
def matching_wb_ooo_article_campaign():
    """WILDBERRIES. Сверяет артикулы ООО с кампаниями ВБ"""
    campaign_list = ad_list()
    DataOooWbArticle.objects.all().update(ad_campaign=None)
    DataOooWbArticle.objects.all().update(wb_campaigns_name=None)
    for campaign in campaign_list:
        header = header_determinant(campaign)
        article_list, wb_campaign_name = wb_articles_in_campaign_and_name(
            campaign, header)
        if article_list:
            for article in article_list:
                if Articles.objects.filter(wb_nomenclature=article).exists():
                    article_obj = Articles.objects.filter(
                        wb_nomenclature=article)[0]
                    if not DataOooWbArticle.objects.filter(
                            wb_article=article_obj).exists():
                        DataOooWbArticle(wb_article=article_obj).save()
                    matching_data = DataOooWbArticle.objects.get(
                        wb_article=article_obj)
                    if matching_data.ad_campaign:
                        if str(campaign) not in str(matching_data.ad_campaign):
                            matching_data.ad_campaign = str(
                                matching_data.ad_campaign) + ', ' + str(campaign)
                    else:
                        matching_data.ad_campaign = campaign
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
                    article_obj = Articles.objects.get(
                        ozon_product_id=article)
                elif Articles.objects.filter(ozon_sku=int(article)).exists():
                    article_obj = Articles.objects.get(
                        ozon_sku=article)
                elif Articles.objects.filter(ozon_fbo_sku_id=int(article)).exists():
                    article_obj = Articles.objects.get(
                        ozon_fbo_sku_id=article)
                elif Articles.objects.filter(ozon_fbs_sku_id=int(article)).exists():
                    article_obj = Articles.objects.get(
                        ozon_fbs_sku_id=article)
                if article_obj:
                    matching_data = DataOooWbArticle.objects.get(
                        wb_article=article_obj)
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


# =========== БЛОК РАБОТЫ С КАМПАНИЯМИ OZON ========== #


@sender_error_to_tg
def ozon_campaign_list():
    """Возвращает список кампаний ОЗОН из базы данных"""
    campaign_data = OzonCampaign.objects.all().values()
    campaign_list = []
    for i in campaign_data:
        campaign_list.append(i['campaign_number'])
    return campaign_list


@sender_error_to_tg
def ozon_adv_bearer_token(payload, header):
    """Получение Bearer токена ОЗОН"""
    url = "https://performance.ozon.ru/api/client/token"
    response = requests.request("POST", url, headers=header, data=payload)
    if response.status_code == 200:
        return json.loads(response.text)['access_token']
    else:
        message = f'Не получил Bearer токен. Ошибка: {response.text}'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message)


@sender_error_to_tg
def ozon_url_for_status(campaign, header, bearer_token):
    """Возвращает статус кампании"""
    url = f'https://performance.ozon.ru/api/client/campaign?campaignIds={campaign}'
    header['Authorization'] = 'Bearer '+bearer_token
    response = requests.request("GET", url, headers=header)
    if response.status_code == 200:
        return json.loads(response.text)['list'][0]['state']
    else:
        time.sleep(10)
        # return ozon_url_for_status(campaign, header, bearer_token)
        message = f'Реклама Озон. Статус кампании {campaign} не выдает. Ошибка: {response.text}'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message, parse_mode='HTML')


@sender_error_to_tg
def ozon_header_determinant(campaign_number):
    """Определяет какой header использовать"""
    header_common = OzonCampaign.objects.get(
        campaign_number=campaign_number).ur_lico.ur_lice_name
    header = ozon_header[header_common]
    return header


@sender_error_to_tg
def ozon_payload_determinant(campaign_number):
    """Определяет какой header использовать"""
    payload_common = OzonCampaign.objects.get(
        campaign_number=campaign_number).ur_lico.ur_lice_name
    payload = ozon_payload[payload_common]
    return payload


@sender_error_to_tg
def ozon_campaign_status():
    """Записывает в базу данных статус кампаний ОЗОН"""
    campaign_list = ozon_campaign_list()

    for campaign in campaign_list:
        header = ozon_header_determinant(campaign)
        payload = ozon_payload_determinant(campaign)
        bearer_token = ozon_adv_bearer_token(payload, header)
        status = ozon_url_for_status(campaign, header, bearer_token)
        campaign_obj = OzonCampaign.objects.get(
            campaign_number=campaign)
        campaign_obj.status = status
        campaign_obj.save()


@sender_error_to_tg
def ozon_status_one_campaign(campaign):
    """Записывает в базу данных статус одной кампании ОЗОН"""

    header = ozon_header_determinant(campaign)
    payload = ozon_payload_determinant(campaign)
    bearer_token = ozon_adv_bearer_token(payload, header)
    status = ozon_url_for_status(campaign, header, bearer_token)
    campaign_obj = OzonCampaign.objects.get(
        campaign_number=campaign)
    campaign_obj.status = status
    campaign_obj.save()


@sender_error_to_tg
def ozon_start_campaign(campaign, header):
    """Запускает рекламную кампанию ОЗОН"""
    url = f'https://performance.ozon.ru/api/client/campaign/{campaign}/v2/activate'
    payload = json.dumps({})
    response = requests.request("POST", url, headers=header, data=payload)
    if response.status_code != 200:
        message = f'Рекламная кампания Озон {campaign} на запустилась. Ошибка: {response.text}'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message, parse_mode='HTML')


@sender_error_to_tg
def ozon_stop_campaign(campaign, header):
    """Останавливает рекламную кампанию ОЗОН"""
    url = f'https://performance.ozon.ru/api/client/campaign/{campaign}/v2/deactivate'
    payload = json.dumps({})
    response = requests.request("POST", url, headers=header, data=payload)
    if response.status_code != 200:
        message = f'Рекламная кампания Озон {campaign} на остановилась. Ошибка: {response.text}'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message, parse_mode='HTML')


@sender_error_to_tg
def ozon_campaign_info():
    """Возвращает два словаря вида: {номер_кампании: статус} и {номер_кампании: id_в системе}"""
    campaign_list = ozon_campaign_list()
    campaign_status = {}
    campaign_id_number = {}

    for campaign in campaign_list:
        header = ozon_header_determinant(campaign)
        payload = ozon_payload_determinant(campaign)
        bearer_token = ozon_adv_bearer_token(payload, header)
        status = ozon_url_for_status(campaign, header, bearer_token)

        id_number = OzonCampaign.objects.get(campaign_number=campaign).pk
        campaign_status[campaign] = status
        campaign_id_number[campaign] = id_number

    return campaign_status, campaign_id_number


@sender_error_to_tg
def ozon_campaign_for_start(stopped_campaign, campaign_id_number):
    """Определяет какую кампанию нужно запустить"""
    start_id = ''
    sorted_dict = {k: v for k, v in sorted(
        campaign_id_number.items(), key=lambda item: item[1])}
    if sorted_dict[stopped_campaign] == max(sorted_dict.values()):
        start_campaign = list(sorted_dict.keys())[0]
    else:
        for i in range(len(list(sorted_dict.values()))):
            if list(sorted_dict.values())[i] == sorted_dict[stopped_campaign]:
                start_id = list(sorted_dict.values())[i+1]
        for camp, value in sorted_dict.items():
            if value == start_id:
                start_campaign = camp
    return start_campaign


@sender_error_to_tg
@app.task
def ozon_start_stop_nessessary_campaign():
    """Останавливает и запускает необходимые кампании"""
    campaign_status_dict, campaign_id_number_dict = ozon_campaign_info()
    if 'CAMPAIGN_STATE_RUNNING' in campaign_status_dict.values():
        for campaign, status in campaign_status_dict.items():

            if status == 'CAMPAIGN_STATE_RUNNING':
                header = ozon_header_determinant(campaign)
                ozon_stop_campaign(campaign, header)
                start_capmaing = ozon_campaign_for_start(
                    campaign, campaign_id_number_dict)
                ozon_start_campaign(start_capmaing, header)
                break
    else:
        start_capmaing = list(campaign_status_dict.keys())[0]
        header = ozon_header_determinant(start_capmaing)
        ozon_start_campaign(start_capmaing, header)
    ozon_campaign_status()
