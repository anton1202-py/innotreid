import json
import math
import os
import time
from datetime import datetime, timedelta

import requests
import telegram
from celery_tasks.celery import app
from dotenv import load_dotenv
from price_system.supplyment import sender_error_to_tg
from reklama.models import (AdvertisingCampaign, CompanyStatistic,
                            OzonCampaign, ProcentForAd, SalesArticleStatistic,
                            WbArticleCommon, WbArticleCompany)

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
def create_articles_company(campaign_number, header):
    """При создании кампании записываются артикулы этой кампании в базу"""
    url = 'https://advert-api.wb.ru/adv/v1/promotion/adverts'
    payload = json.dumps([
        campaign_number
    ])
    response = requests.request("POST", url, headers=header, data=payload)
    articles_list = json.loads(response.text)[0]['autoParams']['nms']
    for article in articles_list:
        if not WbArticleCommon.objects.filter(wb_article=article).exists():
            WbArticleCommon(wb_article=article).save()
        campaign_obj = AdvertisingCampaign.objects.get(
            campaign_number=campaign_number)
        article_obj = WbArticleCommon.objects.get(wb_article=article)
        WbArticleCompany(
            campaign_number=campaign_obj,
            wb_article=article_obj
        ).save()


@sender_error_to_tg
# @app.task
def ad_list():
    """
    Достает список номеров всех компании из базы данных.
    """
    campaign_data = AdvertisingCampaign.objects.all().values()
    campaign_list = []
    for i in campaign_data:
        campaign_list.append(int(i['campaign_number']))
    return campaign_list


@sender_error_to_tg
def db_articles_in_campaign(campaign_number):
    """Достает артикулы, которые есть у компании в базе данных"""
    campaign_obj = AdvertisingCampaign.objects.get(
        campaign_number=campaign_number)
    articles_data = WbArticleCompany.objects.filter(
        campaign_number=campaign_obj
    )
    articles_list = []
    for data in articles_data:
        articles_list.append(int(data.wb_article.wb_article))

    return articles_list


@sender_error_to_tg
def wb_articles_in_campaign(campaign_number, header):
    """Достает артикулы, которые есть у компании в Wildberries"""
    url = 'https://advert-api.wb.ru/adv/v1/promotion/adverts'
    payload = json.dumps([
        campaign_number
    ])
    response = requests.request("POST", url, headers=header, data=payload)
    articles_list = json.loads(response.text)[0]['autoParams']['nms']
    return articles_list


@sender_error_to_tg
def header_determinant(campaign_number):
    """Определяет какой header использовать"""
    header_common = AdvertisingCampaign.objects.get(
        campaign_number=campaign_number).ur_lico.ur_lice_name
    header = wb_header[header_common]

    return header


@sender_error_to_tg
# @app.task
def campaign_article_add():
    """
    Сравнивает списки артикулов в рекламной кампании WB и в рекламной кампании
    базы данных. Если есть расхождения - устранияет их.
    """
    campaign_list = ad_list()
    # Сравниваю данные для каждой кампании между ВБ и Базой ДАнных.
    # Если есть расхождения, устранияю их в базе данных
    for campaign in campaign_list:
        header = header_determinant(campaign)
        campaign_obj = AdvertisingCampaign.objects.get(
            campaign_number=campaign)
        # Смотрю список артикулов на ВБ
        wb_articles_list = wb_articles_in_campaign(campaign, header)
        db_articles_list = db_articles_in_campaign(campaign)
        # Если артикула нет в базе - добавляем
        for article in wb_articles_list:
            if article not in db_articles_list:
                if not WbArticleCommon.objects.filter(wb_article=article).exists():
                    WbArticleCommon(wb_article=article).save()

                article_obj = WbArticleCommon.objects.get(wb_article=article)
                WbArticleCompany(
                    campaign_number=campaign_obj,
                    wb_article=article_obj
                ).save()
        # Если артикула из базы нет в ВБ - удаляем
        for db_article in db_articles_list:
            if db_article not in wb_articles_list:
                article_obj = WbArticleCommon.objects.get(
                    wb_article=db_article)
                wb = WbArticleCompany.objects.filter(
                    campaign_number=campaign_obj,
                    wb_article=article_obj
                )
                # print(wb)
                print('Удалил артикул', article)


@sender_error_to_tg
def count_sum_adv_campaign(data_list: list):
    """
    Подсчитывает сумму в рублях одной рекламной кампании
    data_list - входящий список данных по артикулвм в кампании
    """
    sum = 0

    for data in data_list:
        article_sum = data['statistics']['selectedPeriod']['ordersSumRub']
        sum += article_sum
    return sum


@sender_error_to_tg
def count_sum_orders():
    """Считает сумму заказов каждой рекламной кампании за позавчера"""
    campaign_list = ad_list()

    calculate_data = datetime.now() - timedelta(days=2)
    begin_date = calculate_data.strftime('%Y-%m-%d 00:00:00')
    end_date = calculate_data.strftime('%Y-%m-%d 23:59:59')
    # Словарь вида: {номер_компании: заказов_за_позавчера}
    wb_koef = math.ceil(len(campaign_list)/3)
    url = 'https://suppliers-api.wildberries.ru/content/v1/analytics/nm-report/detail'
    campaign_orders_money_dict = {}
    for i in range(wb_koef):
        # Лист для запроса в эндпоинту ОЗОНа
        start_point = i*3
        finish_point = (i+1)*3
        small_info_list = campaign_list[
            start_point:finish_point]

        for campaign in small_info_list:
            header = header_determinant(campaign)
            article_list = wb_articles_in_campaign(campaign, header)
            payload = json.dumps({
                "brandNames": [],
                "objectIDs": [],
                "tagIDs": [],
                "nmIDs": article_list,
                "timezone": "Europe/Moscow",
                "period": {
                    "begin": begin_date,
                    "end": end_date
                },
                "orderBy": {
                    "field": "ordersSumRub",
                    "mode": "asc"
                },
                "page": 1
            })
            response = requests.request(
                "POST", url, headers=header, data=payload)
            # print(response.text)
            data_list = json.loads(response.text)['data']['cards']
            sum = count_sum_adv_campaign(data_list)
            campaign_orders_money_dict[campaign] = sum
            time.sleep(1)
        time.sleep(61)
        # print(campaign_orders_money_dict)
    return campaign_orders_money_dict


@sender_error_to_tg
def round_up_to_nearest_multiple(num, multiple):
    """
    Округляет до ближайшего заданного числа
    num - входящее для округления число
    multiple - число до которого нужно округлить
    """
    return math.ceil(num / multiple) * multiple


def wb_campaign_budget(campaign, header):
    """
    WILDBERRIES.
    Смотрит бюджет рекламной кампании ВБ.
    """
    url = f'https://advert-api.wb.ru/adv/v1/budget?id={campaign}'
    response = requests.request("GET", url, headers=header)
    budget = json.loads(response.text)['total']
    return budget


@sender_error_to_tg
def replenish_campaign_budget(campaign, budget, header):
    """Пополняет бюджет рекламной кампаний"""
    url = f'https://advert-api.wb.ru/adv/v1/budget/deposit?id={campaign}'
    campaign_obj = AdvertisingCampaign.objects.get(campaign_number=campaign)
    koef = ProcentForAd.objects.get(
        campaign_number=campaign_obj
    ).koefficient
    campaign_budget = math.ceil(budget * koef / 100)
    campaign_budget = round_up_to_nearest_multiple(campaign_budget, 50)

    current_campaign_budget = wb_campaign_budget(campaign, header)

    if campaign_budget < 500:
        campaign_budget = 500
    elif campaign_budget > 10000:
        campaign_budget = 10000

    payload = json.dumps({
        "sum": campaign_budget,
        "type": 1,
        "return": True
    })

    if campaign_budget >= current_campaign_budget:
        # print(
        #     f"Пополнил бюджет кампании {campaign} на {campaign_budget}. Продаж за позавчера было на {budget}")
        response = requests.request("POST", url, headers=header, data=payload)
        if response.status_code == 200:
            message = f"Пополнил бюджет кампании {campaign} на {campaign_budget}. Итого сумма: {json.loads(response.text)['total']}. Продаж за позавчера было на {budget}"
            for user in campaign_budget_users_list:
                bot.send_message(chat_id=user,
                                 text=message, parse_mode='HTML')
        else:
            message = f"Бюджет кампании {campaign} не пополнил. Возможная ошибка: {response.text}. Сумма: {campaign_budget}"
            bot.send_message(chat_id=CHAT_ID_ADMIN,
                             text=message, parse_mode='HTML')
    else:
        # print(f"кампании {campaign} не пополнилась потому что текущий бюджет {current_campaign_budget} > для пополнения {campaign_budget}  Продаж за позавчера было на {budget}")
        message = f"кампании {campaign} не пополнилась потому что текущий бюджет {current_campaign_budget} > для пополнения {campaign_budget}  Продаж за позавчера было на {budget}"
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message, parse_mode='HTML')


@sender_error_to_tg
def check_status_campaign(campaign, header):
    """WILDBERRIES. Проверяет статус рекламной кампаниию"""
    url = f'https://advert-api.wb.ru/adv/v1/promotion/adverts'
    payload = json.dumps([campaign])
    response = requests.request("POST", url, headers=header, data=payload)
    main_data = json.loads(response.text)[0]
    # print(main_data)
    status = main_data['status']
    # print('*************************')
    # print(campaign, status)
    return status


@sender_error_to_tg
def start_add_campaign(campaign, header):
    """Запускает рекламную кампанию"""
    url = f'https://advert-api.wb.ru/adv/v0/start?id={campaign}'
    status = check_status_campaign(campaign, header)
    # print('start_add_campaign', campaign, status)
    if status == 4 or status == 11:
        response = requests.request("GET", url, headers=header)
        if response.status_code != 200:
            message = f"{response.text} {response.status_code}"
            bot.send_message(chat_id=CHAT_ID_ADMIN,
                             text=message, parse_mode='HTML')
    elif status != 4 and status != 11 and status != 9:
        message = f"статус кампании {campaign} = {status}. Не могу запустить кампанию"
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message, parse_mode='HTML')


@sender_error_to_tg
@app.task
def budget_working():
    """Работа с бюджетом компании"""
    campaign_data = count_sum_orders()
    for campaign, budget in campaign_data.items():
        header = header_determinant(campaign)
        replenish_campaign_budget(campaign, budget, header)
        time.sleep(3)
        start_add_campaign(campaign, header)


# budget_working()

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
                         text=message, parse_mode='HTML')


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
