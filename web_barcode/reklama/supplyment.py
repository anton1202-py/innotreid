import json
import math
import os
import time
from datetime import datetime, timedelta

import requests
import telegram
# from celery_tasks.celery import app
from dotenv import load_dotenv
from price_system.supplyment import sender_error_to_tg
from reklama.models import (AdvertisingCampaign, CompanyStatistic,
                            DataOooWbArticle, OooWbArticle, OzonCampaign,
                            ProcentForAd, SalesArticleStatistic,
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
    if response.status_code == 200:
        articles_list = json.loads(response.text)[0]['autoParams']['nms']
        return articles_list
    else:
        message = f'Статус код {response.status_code} - кампания {campaign_number}. Текст ошибки: {response.text}'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message)
        time.sleep(5)
        return wb_articles_in_campaign(campaign_number, header)


@sender_error_to_tg
def header_determinant(campaign_number):
    """Определяет какой header использовать"""
    header_common = AdvertisingCampaign.objects.get(
        campaign_number=campaign_number).ur_lico.ur_lice_name
    header = wb_header[header_common]

    return header


@sender_error_to_tg
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
def count_sum_orders_action(article_list, begin_date, end_date, header):
    """Получает данные о заказах рекламной кампании за позавчера"""
    url = 'https://suppliers-api.wildberries.ru/content/v1/analytics/nm-report/detail'
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
    if response.status_code == 200:
        data_list = json.loads(response.text)['data']['cards']
        return data_list
    else:
        print(
            f'count_sum_orders_action. response.status_code = {response.status_code}')
        text = f'count_sum_orders_action. response.status_code = {response.status_code}'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=text, parse_mode='HTML')
        time.sleep(25)
        return count_sum_orders_action(article_list, begin_date, end_date, header)


@sender_error_to_tg
def count_sum_orders():
    """Считает сумму заказов каждой рекламной кампании за позавчера"""
    campaign_list = ad_list()

    calculate_data = datetime.now() - timedelta(days=2)
    begin_date = calculate_data.strftime('%Y-%m-%d 00:00:00')
    end_date = calculate_data.strftime('%Y-%m-%d 23:59:59')
    # Словарь вида: {номер_компании: заказов_за_позавчера}
    wb_koef = math.ceil(len(campaign_list)/3)

    campaign_orders_money_dict = {}
    for i in range(wb_koef):
        start_point = i*3
        finish_point = (i+1)*3
        small_info_list = campaign_list[
            start_point:finish_point]

        for campaign in small_info_list:
            header = header_determinant(campaign)
            article_list = wb_articles_in_campaign(campaign, header)

            data_list = count_sum_orders_action(
                article_list, begin_date, end_date, header)
            sum = count_sum_adv_campaign(data_list)
            campaign_orders_money_dict[campaign] = sum
            time.sleep(22)
        # time.sleep(61)
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


@sender_error_to_tg
def wb_campaign_budget(campaign, header):
    """
    WILDBERRIES.
    Смотрит бюджет рекламной кампании ВБ.
    """
    url = f'https://advert-api.wb.ru/adv/v1/budget?id={campaign}'
    response = requests.request("GET", url, headers=header)
    if response.status_code == 200:
        budget = json.loads(response.text)['total']
        return budget
    else:
        message = f'Статус код просмотра бюджета {response.status_code} - кампания {campaign}'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message, parse_mode='HTML')
        time.sleep(5)
        return wb_campaign_budget(campaign, header)


def campaign_info_for_budget(campaign, campaign_budget, budget, header):
    """Пополняет бюджет рекламной кампаний"""
    url = f'https://advert-api.wb.ru/adv/v1/budget/deposit?id={campaign}'
    payload = json.dumps({
        "sum": campaign_budget,
        "type": 1,
        "return": True
    })
    response = requests.request("POST", url, headers=header, data=payload)
    if response.status_code == 200:
        message = (f"Пополнил бюджет кампании {campaign} на {campaign_budget}."
                   f"Итого сумма: {json.loads(response.text)['total']}."
                   f"Продаж за позавчера было на {budget}")
        return message
    else:
        message = ('*************************'
                   f'Бюджет кампании {campaign} не пополнил. Возможная ошибка: {response.text}.'
                   f'Статус код: {response.status_code}'
                   '*************************')
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message, parse_mode='HTML')
        return campaign_info_for_budget(campaign, campaign_budget, budget, header)


@sender_error_to_tg
def replenish_campaign_budget(campaign, budget, header):
    """Определяем кампании для пополнения бюджета"""
    campaign_obj = AdvertisingCampaign.objects.get(campaign_number=campaign)
    info_campaign_obj = ProcentForAd.objects.get(
        campaign_number=campaign_obj
    )
    koef = info_campaign_obj.koefficient
    virtual_budjet = info_campaign_obj.virtual_budget

    campaign_budget = math.ceil(budget * koef / 100)
    campaign_budget = round_up_to_nearest_multiple(campaign_budget, 50)
    current_campaign_budget = wb_campaign_budget(campaign, header)

    if campaign_budget < 500:
        common_budget = campaign_budget + virtual_budjet
        if common_budget >= 500:
            campaign_budget = common_budget
        else:
            info_campaign_obj.virtual_budget = common_budget
            info_campaign_obj.save()
            campaign_budget = common_budget

    elif campaign_budget > 10000:
        campaign_budget = 10000

    if campaign_budget >= 500 and campaign_budget >= current_campaign_budget:
        message = campaign_info_for_budget(
            campaign, campaign_budget, budget, header)
        info_campaign_obj.virtual_budget = 0
        info_campaign_obj.save()
    elif campaign_budget < 500:
        message = f'Кампании {campaign} не пополнилась потому общий виртуальный счет меньше 500. {info_campaign_obj.virtual_budget} р.'
    else:
        message = f'Кампании {campaign} не пополнилась потому что текущий бюджет {current_campaign_budget} > для пополнения {campaign_budget}  Продаж за позавчера было на {budget}'

    for user in campaign_budget_users_list:
        bot.send_message(chat_id=user,
                         text=message, parse_mode='HTML')
    if campaign == 15580755:
        text = ('**************************'
                f'Бюджет кампании {campaign} равен {campaign_budget}. Виртуальный счет: {info_campaign_obj.virtual_budget}'
                '**************************')
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=text, parse_mode='HTML')
    # print(message)
    # bot.send_message(chat_id=CHAT_ID_ADMIN,
    #                  text=message, parse_mode='HTML')


@sender_error_to_tg
def check_status_campaign(campaign, header):
    """WILDBERRIES. Проверяет статус рекламной кампаниию"""
    url = f'https://advert-api.wb.ru/adv/v1/promotion/adverts'
    payload = json.dumps([campaign])
    response = requests.request("POST", url, headers=header, data=payload)
    if response.status_code == 200:
        main_data = json.loads(response.text)[0]
        status = main_data['status']
        return status
    elif response.status_code == 504:
        time.sleep(5)
        message = f"РЕКЛАМА ВБ. Статус код на запрос статуса кампании {campaign} = {response.status_code}. Повторяю запрос"
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message, parse_mode='HTML')
        return check_status_campaign(campaign, header)
    else:
        message = f"статус код на запрос статуса кампании {campaign} = {response.status_code}. Возвращаю статус код 11."
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message, parse_mode='HTML')
        return 11


@sender_error_to_tg
def start_add_campaign(campaign, header):
    """WILDBERRIES Запускает рекламную кампанию"""
    url = f'https://advert-api.wb.ru/adv/v0/start?id={campaign}'
    status = check_status_campaign(campaign, header)
    if status:
        if status == 4 or status == 11:
            response = requests.request("GET", url, headers=header)
            if response.status_code != 200:
                message = f"РЕКЛАМА ВБ. Статус код при запуске кампании {campaign}: {response.text} {response.status_code}"
                bot.send_message(chat_id=CHAT_ID_ADMIN,
                                 text=message, parse_mode='HTML')
        elif status != 4 and status != 11 and status != 9:
            message = f"статус кампании {campaign} = {status}. Не могу запустить кампанию"
            bot.send_message(chat_id=CHAT_ID_ADMIN,
                             text=message, parse_mode='HTML')
    else:
        response = requests.request("GET", url, headers=header)
        message = f"статус кампании {campaign} не пришел, но все равно пытаюсь ее запустить"
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message, parse_mode='HTML')


@sender_error_to_tg
def ooo_wb_articles_info(update_date=None, mn_id=0, common_data=None):
    """WILDBERRIES. Получает информацию артикулов ООО ВБ от API WB"""
    if not common_data:
        common_data = []
    if update_date:
        cursor = {
            "limit": 1000,
            "updatedAt": update_date,
            "nmID": mn_id
        }
    else:
        cursor = {
            "limit": 1000,
            "nmID": mn_id
        }

    url = 'https://suppliers-api.wildberries.ru/content/v2/get/cards/list'
    payload = json.dumps(
        {
            "settings": {
                "cursor": cursor,
                "filter": {
                    "withPhoto": -1
                }
            }
        }
    )
    response = requests.request(
        "POST", url, headers=wb_header['ООО Иннотрейд'], data=payload)
    if response.status_code == 200:
        main_answer = json.loads(response.text)
        check_amount = main_answer['cursor']
        article_info = main_answer['cards']
        for data in article_info:
            inner_data = (data['vendorCode'], data['nmID'], data['title'])
            common_data.append(inner_data)
        if len(article_info) == 1000:
            # time.sleep(5)
            ooo_wb_articles_info(
                check_amount['updatedAt'], check_amount['nmID'], common_data)
        return common_data
    else:
        message = f'статус код {response.status_code} у получения инфы всех артикулов ООО ВБ'


# print(ooo_wb_articles_info())

@sender_error_to_tg
def ooo_wb_articles_data():
    """WILDBERRIES. Записывает артикулы ООО ВБ в базу данных"""
    data = ooo_wb_articles_info()
    article_list = []
    for entry in data:
        wb_article, wb_nomenclature, article_title = entry
        article_list.append(wb_nomenclature)
        if not OooWbArticle.objects.filter(wb_article=wb_article).exists():
            OooWbArticle.objects.get_or_create(
                wb_article=wb_article,
                wb_nomenclature=wb_nomenclature,
                article_title=article_title)
    return article_list


@sender_error_to_tg
def wb_ooo_fbo_stock_data():
    """WILDBERRIES. Собирает данные по каждому артикулу. Возвращает список списков со всеми данными"""
    article_list = ooo_wb_articles_data()
    wb_koef = math.ceil(len(article_list)/900)
    calculate_data = datetime.now() - timedelta(days=2)
    begin_date = calculate_data.strftime('%Y-%m-%d 00:00:00')
    end_date = calculate_data.strftime('%Y-%m-%d 23:59:59')
    # Словарь вида: {номер_компании: заказов_за_позавчера}

    url = 'https://seller-analytics-api.wildberries.ru/api/v2/nm-report/detail'

    main_article_data_list = []
    headers = wb_header['ООО Иннотрейд']
    for i in range(wb_koef):
        # Лист для запроса в эндпоинту ОЗОНа
        start_point = i*900
        finish_point = (i+1)*900
        small_info_list = article_list[
            start_point:finish_point]
        payload = json.dumps({
            "brandNames": [],
            "objectIDs": [],
            "tagIDs": [],
            "nmIDs": small_info_list,
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
            "POST", url, headers=headers, data=payload)
        # print(response.text)
        data_list = json.loads(response.text)['data']['cards']
        main_article_data_list.append(data_list)
        time.sleep(21)
    return main_article_data_list

    # print(campaign_orders_money_dict)
