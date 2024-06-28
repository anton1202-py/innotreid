import json
import math
import os
import time
from datetime import datetime, timedelta

import requests
import telegram
from analytika_reklama.models import DailyCampaignParameters
from api_request.wb_requests import (advertisment_campaign_list,
                                     advertisment_statistic_info,
                                     get_budget_adv_campaign)
# from celery_tasks.celery import app
from dotenv import load_dotenv
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg
from reklama.models import (AdvertisingCampaign, CompanyStatistic,
                            DataOooWbArticle, OooWbArticle, OzonCampaign,
                            ProcentForAd, SalesArticleStatistic, UrLico,
                            WbArticleCommon, WbArticleCompany)

from web_barcode.constants_file import (CHAT_ID_ADMIN, CHAT_ID_EU,
                                        TELEGRAM_TOKEN, bot, header_ozon_dict,
                                        header_wb_data_dict, header_wb_dict,
                                        header_yandex_dict,
                                        ozon_adv_client_access_id_dict,
                                        ozon_adv_client_secret_dict,
                                        ozon_api_token_dict,
                                        wb_headers_karavaev, wb_headers_ooo,
                                        yandex_business_id_dict)

campaign_budget_users_list = [CHAT_ID_ADMIN, CHAT_ID_EU]

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
def get_wb_campaign_info(campaign_number, header, attempt=0):
    """Получает информацию о рекламной кампании ВБ"""
    url = 'https://advert-api.wb.ru/adv/v1/promotion/adverts'
    payload = json.dumps([
        campaign_number
    ])
    attempt += 1
    response = requests.request("POST", url, headers=header, data=payload)
    if response.status_code == 200:
        return json.loads(response.text)

    elif response.status_code == 404:
        text = f'Кампания {campaign_number} не найдена в списке кампаний ВБ. Удалите кампанию с сервера. Или проверьте правильно ли записан ее номер'
        for user in campaign_budget_users_list:
            bot.send_message(chat_id=user,
                             text=text, parse_mode='HTML')
        return []
    else:
        time.sleep(5)
        if attempt < 60:
            return get_wb_campaign_info(campaign_number, header, attempt)
        else:
            text = f'Данные кампании {campaign_number} были запрошены 50 раз. Статус код {response.status_code}'
            bot.send_message(chat_id=CHAT_ID_ADMIN,
                             text=text, parse_mode='HTML')
            return []


def get_campaign_article_from_statistic(campaign_number, header):
    """Получаем список артикулов кампании из статистики"""
    date_today = datetime.now().strftime('%Y-%m-%d')
    date_early_raw = datetime.now() - timedelta(20)
    date_early = date_early_raw.strftime('%Y-%m-%d')

    adv_list = [
        {
            "id": campaign_number,
            "interval": {
                "begin": date_early,
                "end": date_today
            }
        }
    ]
    main_data = advertisment_statistic_info(adv_list, header)
    article_list = []
    booster_info = main_data[0]['boosterStats']

    for article in booster_info:
        if article['nm'] not in article_list:
            article_list.append(article['nm'])
    return article_list


@sender_error_to_tg
def wb_articles_in_campaign(campaign_number, header, counter=0):
    """Достает артикулы, которые есть у компании в Wildberries"""
    campaign_data = get_wb_campaign_info(campaign_number, header)
    counter += 1
    if campaign_data:
        articles_list = []
        if 'autoParams' in campaign_data[0]:
            articles_list = campaign_data[0]['autoParams']['nms']
        elif 'unitedParams' in campaign_data[0]:
            articles_list = campaign_data[
                0]['unitedParams'][0]['nms']
        elif 'params' in campaign_data[0]:
            articles_data = campaign_data[
                0]['params'][0]
            for article in articles_data:
                articles_list.append(article['nm'])
        if articles_list == None:
            articles_list = get_campaign_article_from_statistic(
                campaign_number, header)
        return articles_list
    else:
        return []


@sender_error_to_tg
def wb_articles_in_campaign_and_name(campaign_number, header, counter=0):
    """Достает артикулы, которые есть у компании в Wildberries"""
    campaign_data = get_wb_campaign_info(campaign_number, header)
    if campaign_data:
        articles_list = []
        if 'autoParams' in campaign_data[0]:
            articles_list = campaign_data[0]['autoParams']['nms']
        elif 'unitedParams' in campaign_data[0]:
            articles_list = campaign_data[
                0]['unitedParams'][0]['nms']
        elif 'params' in campaign_data[0]:
            articles_data = campaign_data[
                0]['params'][0]
            for article in articles_data:
                articles_list.append(article['nm'])

        if articles_list == None:
            articles_list = get_campaign_article_from_statistic(
                campaign_number, header)
        return articles_list, campaign_number
    else:
        return [], ''


# @sender_error_to_tg
def header_determinant(campaign_number):
    """Определяет какой header использовать"""
    header_common = AdvertisingCampaign.objects.get(
        campaign_number=campaign_number).ur_lico.ur_lice_name
    header = header_wb_dict[header_common]

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
    url = 'https://seller-analytics-api.wildberries.ru/api/v2/nm-report/detail'
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

            # if article_list:
            if AdvertisingCampaign.objects.filter(campaign_number=campaign).exists():
                data_list = count_sum_orders_action(
                    article_list, begin_date, end_date, header)
                sum = count_sum_adv_campaign(data_list)
                campaign_orders_money_dict[campaign] = sum

                time.sleep(22)
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
def wb_campaign_budget(campaign, header, counter=0):
    """
    WILDBERRIES.
    Смотрит бюджет рекламной кампании ВБ.
    """
    url = f'https://advert-api.wb.ru/adv/v1/budget?id={campaign}'
    response = requests.request("GET", url, headers=header)
    counter += 1
    if response.status_code == 200:
        budget = json.loads(response.text)['total']
        return budget
    elif response.status_code != 200 and counter <= 50:
        time.sleep(10)
        return wb_campaign_budget(campaign, header, counter)
    else:
        message = f'Статус код просмотра бюджета {response.status_code} - кампания {campaign}'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message, parse_mode='HTML')


def check_campaign_type(header, campaign):
    """Проверяет тип рекламной кампании"""
    campaigns_data = advertisment_campaign_list(header)


def view_statistic_adv_campaign(header, campaign):
    """Возвращает статистику показов рекламной кампании за вчерашний день"""
    statistic_date_raw = datetime.now() - timedelta(days=2)
    statistic_date = statistic_date_raw.strftime('%Y-%m-%d')
    ur_lico = ''
    for ur_lico_data, header_data in header_wb_dict.items():
        if header_data == header:
            ur_lico = ur_lico_data

    if DailyCampaignParameters.objects.filter(
            campaign__ur_lico__ur_lice_name=ur_lico,
            campaign__campaign_number=str(campaign)
    ).exists():
        statistic_obj_raw = DailyCampaignParameters.objects.filter(
            campaign__ur_lico__ur_lice_name=ur_lico,
            campaign__campaign_number=campaign
        ).order_by('-id')
        statistic_obj = statistic_obj_raw.first()
        return statistic_obj
    else:
        return None


def current_budget_adv_campaign(header, campaign):
    """Определяет бюджет рекламной кампании"""
    budget_data = get_budget_adv_campaign(header, campaign)
    if budget_data:
        return budget_data['total']
    else:
        return 'Не определено'


def campaign_info_for_budget(campaign, campaign_budget, budget, koef, header, attempt_counter=0):
    """
    Пополняет бюджет рекламной кампаний
    campaign - id кампании
    campaign_budget - бюджет, на который пополнится кампания
    budget - сумма заказов артикулов из этой кампании за позавчера
    koef - коэффициент от суммы заказов, который идет на рекламу
    header - header юр. лица для запроса к  АПИ ВБ
    """
    campaign_budget = round_up_to_nearest_multiple(campaign_budget, 50)
    url = f'https://advert-api.wb.ru/adv/v1/budget/deposit?id={campaign}'
    payload = json.dumps({
        "sum": campaign_budget,
        "type": 1,
        "return": True
    })
    response = requests.request("POST", url, headers=header, data=payload)
    time.sleep(5)
    attempt_counter += 1
    if response.status_code == 200:
        time.sleep(5)
        current_budget = current_budget_adv_campaign(header, campaign)
        view_statistic = view_statistic_adv_campaign(header, campaign)
        if view_statistic:
            message = (f"Пополнил {campaign}: {view_statistic.campaign.campaign_name}. Продаж {budget} руб. Показов: {view_statistic.views}. Пополнил на {campaign_budget}руб ({koef}%)"
                       f"Итого бюджет: {current_budget}."
                       f"Дата статистики: {view_statistic.statistic_date}")
        else:
            message = (f"Пополнил {campaign}. Продаж {budget} руб. Пополнил на {campaign_budget}руб ({koef}%)"
                       f"Итого бюджет: {current_budget}.")
        return message
    else:
        if attempt_counter <= 50:
            return campaign_info_for_budget(campaign, campaign_budget, budget, koef, header, attempt_counter)
        else:
            message = (f'Бюджет кампании {campaign} не пополнил.'
                       f'Пытался пополнить 50 раз - возвращалась ошибка.')
            return message


@sender_error_to_tg
def replenish_campaign_budget(campaign, budget, header):
    """
    Определяем кампании для пополнения бюджета
    campaign - id рекламной кампании
    budget - сумма заказов текущей рекламной кампании за позавчера
    header - header текущего юр лица для связи с АПИ ВБ
    """
    now_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    campaign_obj = AdvertisingCampaign.objects.get(campaign_number=campaign)
    info_campaign_obj = ProcentForAd.objects.get(
        campaign_number=campaign_obj
    )
    koef = info_campaign_obj.koefficient
    virtual_budjet = info_campaign_obj.virtual_budget

    campaign_budget = math.ceil(budget * koef / 100)
    campaign_budget = round_up_to_nearest_multiple(campaign_budget, 50)
    add_to_virtual_bill = round_up_to_nearest_multiple(campaign_budget, 50)
    current_campaign_budget = wb_campaign_budget(campaign, header)

    if campaign_budget < 1000:
        common_budget = campaign_budget + virtual_budjet
        if common_budget >= 1000:
            campaign_budget = common_budget
        else:
            # Женя попросил безусловное пополнение раз в день.
            info_campaign_obj.virtual_budget = common_budget + 30
            info_campaign_obj.virtual_budget_date = now_date
            info_campaign_obj.save()
            campaign_budget = common_budget

    elif campaign_budget > 10000:
        campaign_budget = 10000

    message = ''
    view_count = ''
    campaign_name = ''
    view_statistic = view_statistic_adv_campaign(header, campaign)

    if view_statistic:
        view_count = view_statistic.views
        campaign_name = view_statistic.campaign.campaign_name
    if campaign_budget >= 1000 and campaign_budget >= current_campaign_budget:
        message = campaign_info_for_budget(
            campaign, campaign_budget, budget, koef, header)
        if 'Пытался' not in message:
            info_campaign_obj.virtual_budget = 0
            info_campaign_obj.campaign_budget_date = now_date
        else:
            info_campaign_obj.virtual_budget += campaign_budget
        info_campaign_obj.virtual_budget_date = now_date
        info_campaign_obj.save()

    elif campaign_budget < 1000:
        message = (f'{campaign}: {campaign_name} - продаж {budget} руб. Показов: {view_count}. Начислено на виртуальный счет: {add_to_virtual_bill}руб ({koef}%). Баланс: {info_campaign_obj.virtual_budget}р.'
                   f'Дата статистики: {view_statistic.statistic_date}')
    else:
        message = (f'{campaign}: {campaign_name} - продаж {budget} руб. Показов: {view_count}. Не пополнилась. Текущий бюджет {current_campaign_budget}р > бюджета для пополнения {campaign_budget}р'
                   f'Дата статистики: {view_statistic.statistic_date}')
    return message


@sender_error_to_tg
def check_status_campaign(campaign, header, counter=0):
    """WILDBERRIES. Проверяет статус рекламной кампаниию"""
    url = f'https://advert-api.wb.ru/adv/v1/promotion/adverts'
    payload = json.dumps([campaign])
    counter += 1
    response = requests.request("POST", url, headers=header, data=payload)
    if response.status_code == 200:
        main_data = json.loads(response.text)[0]
        status = main_data['status']
        return status
    elif response.status_code != 200 and counter <= 50:
        time.sleep(10)
        return check_status_campaign(campaign, header, counter)
    else:
        message = f"статус код на запрос статуса кампании {campaign} = {response.status_code}. Возвращаю статус код 11."
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message, parse_mode='HTML')
        return 11


@sender_error_to_tg
def campaing_current_budget(campaign, header):
    """Проверяет текущий бюджет кампании"""
    url = f'https://advert-api.wb.ru/adv/v1/budget?id={campaign}'
    response = requests.request("GET", url, headers=header)
    if response.status_code == 200:
        budget = json.loads(response.text)['total']
        return budget
    elif response.status_code == 400:
        message = f"Просмотр бюджета кампании {campaign}.Ошибка 400 - ошибочный запрос"
        bot.send_message(chat_id=CHAT_ID_ADMIN, text=message[:4092])
        return 100
    elif response.status_code == 401:
        message = f"Просмотр бюджета кампании {campaign}.Ошибка 401 - пользователь не авторизован"
        bot.send_message(chat_id=CHAT_ID_ADMIN, text=message[:4092])
        return 0
    elif response.status_code == 404:
        message = f"Просмотр бюджета кампании {campaign}.Ошибка 404 - кампания не найдена"
        bot.send_message(chat_id=CHAT_ID_ADMIN, text=message[:4092])
        return 0
    else:
        return campaing_current_budget(campaign, header)


@sender_error_to_tg
def start_add_campaign(campaign, header, counter=0):
    """WILDBERRIES Запускает рекламную кампанию"""
    url = f'https://advert-api.wb.ru/adv/v0/start?id={campaign}'
    status = check_status_campaign(campaign, header)
    budget = campaing_current_budget(campaign, header)
    counter += 1
    if status and counter <= 50:
        if status == 4 or status == 11:
            if budget > 0:
                response = requests.request("GET", url, headers=header)
                if response.status_code != 200 and response.status_code != 422:
                    start_add_campaign(campaign, header, counter)
                elif response.status_code == 404:
                    message = f"РЕКЛАМА ВБ. Статус код при запуске кампании {campaign}: {response.status_code}. Кампания не найдена"
                    bot.send_message(chat_id=CHAT_ID_ADMIN,
                                     text=message[:4092])

        elif status != 4 and status != 11 and status != 9:
            message = f"статус кампании {campaign} = {status}. Не могу запустить кампанию"
            bot.send_message(chat_id=CHAT_ID_ADMIN, text=message[:4092])
    else:
        response = requests.request("GET", url, headers=header)
        message = f"статус кампании {campaign} не пришел, но все равно пытаюсь ее запустить"
        bot.send_message(chat_id=CHAT_ID_ADMIN, text=message[:4092])


@sender_error_to_tg
def sort_message_list(messages_list: list):
    """
    WILDBERRIES.
    Сортирует список сообщений на пополненные и не пополненные кампании
    messages_list - список сообщений по каждой кампании - пополнилась
    она или нет.
    """
    replenish_messages = 'Бюджет пополнил:'
    unreplenish_messages = 'Бюджет кампаний не пополнен:'
    for message in messages_list:
        if 'Пополнил' in message:
            replenish_messages += f'\n\n{message}'
        else:
            unreplenish_messages += f'\n\n{message}'
    messages = [replenish_messages, unreplenish_messages]
    return messages


@sender_error_to_tg
def send_common_message(messages_list: list):
    """
    WILDBERRIES.
    Отправляет общие сообщение о не запущенных рекламных кампаниях
    И о запущенных
    messages_list - список сообщений по каждой кампании - пополнилась
    она или нет.
    """
    messages = sort_message_list(messages_list)
    for message in messages:
        for user in campaign_budget_users_list:
            bot.send_message(chat_id=user,
                             text=message[:4094], parse_mode='HTML')


@sender_error_to_tg
def ooo_wb_articles_info(update_date=None, mn_id=0, common_data=None):
    """WILDBERRIES. Получает информацию артикулов ООО ВБ от API WB"""
    if not common_data:
        common_data = []
    if update_date:
        cursor = {
            "limit": 100,
            "updatedAt": update_date,
            "nmID": mn_id
        }
    else:
        cursor = {
            "limit": 100,
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
        "POST", url, headers=header_wb_dict['ООО Иннотрейд'], data=payload)
    if response.status_code == 200:
        main_answer = json.loads(response.text)
        check_amount = main_answer['cursor']
        article_info = main_answer['cards']
        for data in article_info:
            inner_data = (data['vendorCode'], data['nmID'], data['title'])
            common_data.append(inner_data)
        if len(article_info) == 100:
            # time.sleep(5)
            ooo_wb_articles_info(
                check_amount['updatedAt'], check_amount['nmID'], common_data)
        return common_data


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
def get_wb_ooo_stock_data(header, info_list):
    """Получает данные от метода api/v2/nm-report/detail"""
    calculate_data = datetime.now() - timedelta(days=2)
    begin_date = calculate_data.strftime('%Y-%m-%d 00:00:00')
    end_date = calculate_data.strftime('%Y-%m-%d 23:59:59')
    url = 'https://seller-analytics-api.wildberries.ru/api/v2/nm-report/detail'
    payload = json.dumps({
        "brandNames": [],
        "objectIDs": [],
        "tagIDs": [],
        "nmIDs": info_list,
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
    elif response.status_code == 404:
        text = f'reklama.supplyment.get_wb_ooo_stock_data. Статус код = {response.status_code}. Какая-то серьезная ошибка'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=text, parse_mode='HTML')
    else:
        text = f'reklama.supplyment.get_wb_ooo_stock_data. Статус код = {response.status_code}'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=text, parse_mode='HTML')
        time.sleep(21)
        return get_wb_ooo_stock_data(header, info_list)


@sender_error_to_tg
def wb_ooo_fbo_stock_data():
    """WILDBERRIES. Собирает данные по каждому артикулу. Возвращает список списков со всеми данными"""
    article_list = ooo_wb_articles_data()
    wb_koef = math.ceil(len(article_list)/900)
    main_article_data_list = []
    header = header_wb_dict['ООО Иннотрейд']
    for i in range(wb_koef):
        # Лист для запроса в эндпоинту ОЗОНа
        start_point = i*900
        finish_point = (i+1)*900
        small_info_list = article_list[
            start_point:finish_point]
        data_list = get_wb_ooo_stock_data(header, small_info_list)
        main_article_data_list.append(data_list)
        time.sleep(21)
    return main_article_data_list


@sender_error_to_tg
def ooo_wb_articles_to_dataooowbarticles():
    """WILDBERRIES. Записывает артикулы ООО ВБ в базу данных"""
    article_list = Articles.objects.filter(company='ООО Иннотрейд')
    for article in article_list:
        if not DataOooWbArticle.objects.filter(wb_article=article).exists():
            DataOooWbArticle.objects.get_or_create(
                wb_article=article)


# ========== РАБОТА С РЕКЛАМНЫМИ КАМПАНИЯМИ ОЗОН ========= #

@sender_error_to_tg
def access_token(ur_lico):
    """
    Получение Bearer токена для работы с рекламным кабинетом.
    Выдается при каждом запросе в рекламный кабинет юр. лица.
    """
    url = "https://performance.ozon.ru/api/client/token"

    payload = json.dumps({
        "client_id": ozon_adv_client_access_id_dict[ur_lico],
        "client_secret": ozon_adv_client_secret_dict[ur_lico],
        "grant_type": "client_credentials"
    })

    response = requests.request(
        "POST", url, headers=header_ozon_dict[ur_lico], data=payload)
    return json.loads(response.text)['access_token']


@sender_error_to_tg
def ozon_get_adv_campaign_list(ur_lico):
    """
    Получает список рекламных кампаний входящего юр лица
    """
    url = 'https://performance.ozon.ru:443/api/client/campaign'
    header = header_ozon_dict[ur_lico]
    header['Authorization'] = f'Bearer {access_token(ur_lico)}'
    response = requests.request("GET", url, headers=header)
    ozon_adv_list = json.loads(response.text)['list']
    return ozon_adv_list


@sender_error_to_tg
def ozon_get_campaign_data(ur_lico):
    """Получает данные рекламных кампаний ОЗОН. ID и название"""
    ozon_adv_list = ozon_get_adv_campaign_list(ur_lico)
    ozon_adv_info_dict = {}
    if ozon_adv_list:
        for i in ozon_adv_list:
            ozon_adv_info_dict[i['id']] = {'Название': i['title']}

    return ozon_adv_info_dict


@sender_error_to_tg
def ozon_get_articles_data_adv_campaign(ur_lico, campaign, header):
    """Получает данные рекламной кампании"""
    url = f'https://performance.ozon.ru:443/api/client/campaign/{campaign}/objects'
    response = requests.request("GET", url, headers=header)
    articles_list = []
    if response.status_code == 200:
        articles_list = json.loads(response.text)['list']
    elif response.status_code == 404:
        print(f'Проверьте статус рекламной кампании {campaign}')
    return articles_list


@sender_error_to_tg
def ozon_get_articles_in_adv_campaign(ur_lico, campaign, header):
    """Получает список артикулов рекламной кампании"""
    articles_data_list = ozon_get_articles_data_adv_campaign(
        ur_lico, campaign, header)
    articles_list = []
    for data in articles_data_list:
        articles_list.append(data['id'])
    return articles_list


@sender_error_to_tg
def ozon_adv_campaign_articles_name_data(ur_lico):
    """
    Возвращает словарь с данными кампании по артикулам и названию
    Вид словаря: {кампания: {'Название': 'Название кампании', 'Артикулы': [Список артикулов]}}
    """
    campaigns_data = ozon_get_campaign_data(ur_lico)
    header = header_ozon_dict[ur_lico]
    header['Authorization'] = f'Bearer {access_token(ur_lico)}'
    for campaign, data in campaigns_data.items():
        articles_list = ozon_get_articles_in_adv_campaign(
            ur_lico, campaign, header)
        data['Артикулы'] = articles_list
    return campaigns_data
