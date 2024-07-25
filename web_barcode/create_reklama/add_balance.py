import json
import math
import os
import time
from datetime import datetime, timedelta

import requests
import telegram
from analytika_reklama.models import DailyCampaignParameters
from api_request.wb_requests import (advertisment_campaign_list,
                                     get_budget_adv_campaign)
from create_reklama.models import (CreatedCampaign, ProcentForAd,
                                   ReplenishWbCampaign,
                                   SenderStatisticDaysAmount)
from django.db.models import Sum
# from celery_tasks.celery import app
from dotenv import load_dotenv
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg
from reklama.models import DataOooWbArticle, OooWbArticle, UrLico

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


@sender_error_to_tg
def ad_list():
    """
    Достает список номеров всех компании из базы данных.
    Возвращает словарь типа {ur_lico: [article_list]}
    """
    campaign_data = CreatedCampaign.objects.all().values(
        'campaign_number', 'ur_lico__ur_lice_name')
    campaign_dict = {}
    for i in campaign_data:
        if i['ur_lico__ur_lice_name'] in campaign_dict:
            campaign_dict[i['ur_lico__ur_lice_name']].append(
                int(i['campaign_number']))
        else:
            campaign_dict[i['ur_lico__ur_lice_name']] = [
                int(i['campaign_number'])]
    return campaign_dict


# @sender_error_to_tg
# def db_articles_in_campaign(campaign_number):
#     """Достает артикулы, которые есть у компании в базе данных"""
#     campaign_obj = CreatedCampaign.objects.get(
#         campaign_number=campaign_number)
#     articles_data = WbArticleCompany.objects.filter(
#         campaign_number=campaign_obj
#     )
#     articles_list = []
#     for data in articles_data:
#         articles_list.append(int(data.wb_article.wb_article))
#     return articles_list


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


@sender_error_to_tg
def header_determinant(campaign_number):
    """Определяет какой header использовать"""
    header_common = CreatedCampaign.objects.get(
        campaign_number=campaign_number).ur_lico.ur_lice_name
    header = header_wb_dict[header_common]
    return header


@sender_error_to_tg
def count_sum_adv_campaign(data_list: list):
    """
    Подсчитывает сумму в рублях одной рекламной кампании
    data_list - входящий список данных по артикулвм в кампании
    """
    sum = 0
    if data_list:
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
    campaign_dict = ad_list()
    calculate_data = datetime.now() - timedelta(days=1)
    begin_date = calculate_data.strftime('%Y-%m-%d 00:00:00')
    end_date = calculate_data.strftime('%Y-%m-%d 23:59:59')
    # Словарь вида: {номер_компании: заказов_за_позавчера}
    returned_campaign_orders_money_dict = {}
    for ur_lico, campaign_list in campaign_dict.items():
        ur_lico_obj = UrLico.objects.get(ur_lice_name=ur_lico)

        campaign_orders_money_dict = {}
        print(len(campaign_list))
        n = len(campaign_list)
        for campaign in campaign_list:
            header = header = header_wb_dict[ur_lico]
            article_for_analyz = ''
            if CreatedCampaign.objects.filter(ur_lico=ur_lico_obj, campaign_number=campaign).exists():
                campaign_article = CreatedCampaign.objects.get(
                    ur_lico=ur_lico_obj, campaign_number=campaign).articles_name
                if campaign_article:
                    if type(campaign_article) == list:
                        article_for_analyz = campaign_article
                    else:
                        article_for_analyz = [int(campaign_article)]
                    data_list = count_sum_orders_action(
                        article_for_analyz, begin_date, end_date, header)
                    sum = 0
                    if data_list:
                        sum = count_sum_adv_campaign(data_list)
                    campaign_orders_money_dict[campaign] = sum
                    time.sleep(22)
            n -= 1
            print(n)
        returned_campaign_orders_money_dict[ur_lico] = campaign_orders_money_dict
    return returned_campaign_orders_money_dict


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
    days_delta = SenderStatisticDaysAmount.objects.get(id=1).days_amount + 1
    statistic_date_finish = datetime.now()
    statistic_date_start = statistic_date_finish - timedelta(days=days_delta)
    ur_lico = ''
    for ur_lico_data, header_data in header_wb_dict.items():
        if header_data == header:
            ur_lico = ur_lico_data

    if DailyCampaignParameters.objects.filter(
            campaign__ur_lico__ur_lice_name=ur_lico,
            campaign__campaign_number=str(campaign),
            statistic_date__gt=statistic_date_start,
            statistic_date__lt=statistic_date_finish
    ).exists():
        statistic_data = DailyCampaignParameters.objects.filter(
            campaign__ur_lico__ur_lice_name=ur_lico,
            campaign__campaign_number=campaign,
            statistic_date__gt=statistic_date_start,
            statistic_date__lt=statistic_date_finish
        ).aggregate(
            total_views=Sum('views'),
            total_clicks=Sum('clicks'),
            total_orders=Sum('orders')
        )

        # Обрабатываем случай, если total_views = None
        total_views = statistic_data['total_views'] or 0
        # Обрабатываем случай, если total_clicks = None
        total_clicks = statistic_data['total_clicks'] or 0

        # Вычисляем total_ctr
        total_ctr = round((total_clicks / total_views *
                          100), 2) if total_views > 0 else 0

        # Добавляем total_ctr в результат
        statistic_data['total_ctr'] = total_ctr

        return statistic_data
    else:
        return None


def current_budget_adv_campaign(header, campaign):
    """Определяет бюджет рекламной кампании"""
    budget_data = get_budget_adv_campaign(header, campaign)
    if budget_data:
        return budget_data['total']
    else:
        return 'Не определено'


def statistic_campaign_budget_replenish(campaign_obj, campaign_budget):
    """
    Записывает данные в таблицу со статистикой пополнения бюджета рекламной кампании
    Входящие данные:
    campaign_obj - объект кампании для пополнения бюджета
    campaign_budget - бюджет, на который пополняется кампания
    """
    date_today = datetime.now()
    ReplenishWbCampaign(
        campaign_number=campaign_obj,
        sum=campaign_budget,
        replenish_date=date_today
    ).save()


def campaign_info_for_budget(campaign, campaign_budget, budget, koef, header, campaign_obj, attempt_counter=0):
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
        # Записывает в БД статистику пополнения бюджета
        statistic_campaign_budget_replenish(campaign_obj, campaign_budget)
        time.sleep(5)
        current_budget = current_budget_adv_campaign(header, campaign)
        view_statistic = view_statistic_adv_campaign(header, campaign)
        # Показы
        view_count = ''
        # Переходы
        view_clicks = ''
        # CTR
        view_ctr = ''
        # Заказы
        view_orders = ''
        statistic_date = ''
        if view_statistic:
            # Показы
            view_count = view_statistic['total_views']
            # Переходы
            view_clicks = view_statistic['total_clicks']
            # CTR
            view_ctr = view_statistic['total_ctr']
            # Заказы
            view_orders = view_statistic['total_orders']
            statistic_date = SenderStatisticDaysAmount.objects.get(
                id=1).days_amount
        if view_statistic:
            message = (f"Пополнил {campaign}: {campaign_obj.campaign_name}. \nПродаж {budget} руб.\nПоказов: {view_count}.\nПереходов: {view_clicks}.\nCTR: {view_ctr}.\nЗаказов: {view_orders}. \nПополнил на {campaign_budget}руб ({koef}%)"
                       f"\nИтого бюджет: {current_budget}."
                       f"\nСтатистика за последние : {statistic_date} дней")
        else:
            message = (f"Пополнил {campaign}. \nПродаж {budget} руб. \nПополнил на {campaign_budget}руб ({koef}%)"
                       f"\nИтого бюджет: {current_budget}.")
        return message
    elif response.status_code == 401:
        message = (f'Кампания {campaign} не пополнил.'
                   f'Ошибка авторизации {response.text}')
        return message
    elif response.status_code == 400:
        message = (f'Кампания {campaign} не пополнил.'
                   f'Пытался пополнить. Ошибка {response.text}')
        return message
    else:
        if attempt_counter <= 10:
            return campaign_info_for_budget(campaign, campaign_budget, budget, koef, header, campaign_obj, attempt_counter)
        else:
            message = (f'Бюджет кампании {campaign} не пополнил.'
                       f'Пытался пополнить 10 раз - возвращалась ошибка. {response.text}')
            return message


@sender_error_to_tg
def replenish_campaign_budget(campaign, budget, header, campaign_obj):
    """
    Определяем кампании для пополнения бюджета
    campaign - id рекламной кампании
    budget - сумма заказов текущей рекламной кампании за позавчера
    header - header текущего юр лица для связи с АПИ ВБ
    """
    now_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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
            # Женя попросил безусловное пополнение ВС раз в день.
            info_campaign_obj.virtual_budget = common_budget + 30
            info_campaign_obj.virtual_budget_date = now_date
            info_campaign_obj.save()
            campaign_budget = common_budget

    elif campaign_budget > 10000:
        campaign_budget = 10000

    message = ''
    # Показы
    view_count = ''
    # Переходы
    view_clicks = ''
    # CTR
    view_ctr = ''
    # Заказы
    view_orders = ''
    statistic_date = ''
    view_statistic = view_statistic_adv_campaign(header, campaign)

    if view_statistic:
        # Показы
        view_count = view_statistic['total_views']
        # Переходы
        view_clicks = view_statistic['total_clicks']
        # CTR
        view_ctr = view_statistic['total_ctr']
        # Заказы
        view_orders = view_statistic['total_orders']
        statistic_date = SenderStatisticDaysAmount.objects.get(
            id=1).days_amount
    if campaign_budget >= 1000 and campaign_budget >= current_campaign_budget:
        message = campaign_info_for_budget(
            campaign, campaign_budget, budget, koef, header, campaign_obj)
        if 'Пытался' not in message:
            info_campaign_obj.virtual_budget = 0
            info_campaign_obj.campaign_budget_date = now_date
        else:
            info_campaign_obj.virtual_budget += campaign_budget
        info_campaign_obj.virtual_budget_date = now_date
        info_campaign_obj.save()

    elif campaign_budget < 1000:
        message = (f'{campaign}: {campaign_obj.campaign_name}. \nПродаж {budget} руб.\nПоказов: {view_count}.\nПереходов: {view_clicks}.\nCTR: {view_ctr}.\nЗаказов: {view_orders}.\nНачислено на виртуальный счет: {add_to_virtual_bill}руб ({koef}%).\nБаланс ВС: {info_campaign_obj.virtual_budget}р.'
                   f'\nТекущий баланс кампании: {current_campaign_budget}.\nСтатистика за последние: {statistic_date} дней')
    else:
        message = (f'{campaign}: {campaign_obj.campaign_name}. \nПродаж {budget} руб.\nПоказов: {view_count}.\nПереходов: {view_clicks}.\nCTR: {view_ctr}.\nЗаказов: {view_orders}. Не пополнилась.\nТекущий бюджет {current_campaign_budget}р > бюджета для пополнения {campaign_budget}р'
                   f'\nТекущий баланс кампании: {current_campaign_budget}.\nСтатистика за последние: {statistic_date} дней')
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
        message_count = math.ceil(len(message)/4000)
        for i in range(message_count):
            start_point = i*4000
            finish_point = (i+1)*4000
            message_for_send = message[
                start_point:finish_point]
            time.sleep(1)
            for user in campaign_budget_users_list:
                bot.send_message(chat_id=user,
                                 text=message_for_send)


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
    data = Articles.objects.filter(company='ООО Иннотрейд')
    article_list = []
    for article_obj in data:
        article_list.append(article_obj.wb_nomenclature)
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
