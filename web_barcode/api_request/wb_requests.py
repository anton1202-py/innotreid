import json
import time

import requests
from api_request.common_func import api_retry_decorator
from price_system.supplyment import sender_error_to_tg

from web_barcode.constants_file import CHAT_ID_ADMIN, bot


@sender_error_to_tg
def wb_article_data_from_api(header, update_date=None, mn_id=0, common_data=None, counter=0):
    """Получаем данные всех артикулов в ВБ"""
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
        "POST", url, headers=header, data=payload)

    counter += 1
    if response.status_code == 200:
        all_data = json.loads(response.text)["cards"]
        check_amount = json.loads(response.text)['cursor']
        for data in all_data:
            common_data.append(data)
        if len(json.loads(response.text)["cards"]) == 100:
            # time.sleep(1)
            return wb_article_data_from_api(header,
                                            check_amount['updatedAt'], check_amount['nmID'], common_data, counter)
        return common_data
    elif response.status_code != 200 and counter <= 50:
        return wb_article_data_from_api(header, update_date, mn_id, common_data, counter)
    else:
        message = f'статус код {response.status_code} у получения инфы всех артикулов api_request.wb_article_data'
        bot.send_message(chat_id=CHAT_ID_ADMIN, text=message)


@sender_error_to_tg
def wb_sales_statistic(header, check_date, attempt=0):
    """Получаем данные всех артикулов в ВБ. Максимум 1 запрос в минут"""
    url = f'https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom={check_date}&flag=1'

    response = requests.request(
        "GET", url, headers=header)
    attempt += 1
    message = ''
    time.sleep(2)
    if attempt <= 50:
        if response.status_code == 200:
            all_data = json.loads(response.text)
            return all_data
        else:
            time.sleep(65)
            return wb_sales_statistic(header, check_date, attempt)
    elif response.status_code == 403:
        message = f'статус код {response.status_code}. Доступ запрещен'
    elif response.status_code == 429:
        message = f'статус код {response.status_code}. Слишком много запросов'
    elif response.status_code == 401:
        message = f'статус код {response.status_code}. Не авторизован'
    else:
        message = f'статус код {response.status_code} у получения инфы всех артикулов ООО ВБ'

    if message:
        message = f'api_request.wb_sales_statistic. {message}'
        bot.send_message(chat_id=CHAT_ID_ADMIN, text=message)


# =========== API ЗАПРОСЫ ПРОДВИЖЕНИЯ WILDBERRIES ========== #

@api_retry_decorator
def advertisment_campaign_list(header):
    """
    Получаем списки рекламных кампаний
    Допускается 5 запросов в секунду
    """
    time.sleep(0.3)
    url = 'https://advert-api.wb.ru/adv/v1/promotion/count'
    response = requests.request("GET", url, headers=header)
    return response


@api_retry_decorator
def advertisment_campaigns_list_info(adv_list: list, header: str):
    """
    Получаем информацию о каждой рекламной кампании, которая находится
    в списке adv_list

    переменные:
    adv_list - список рекламных кампаний
    header - хедер для запроса

    return: response от запроса к методу https://advert-api.wb.ru/adv/v1/promotion/adverts

    Допускается 5 запросов в секунду.
    Список ID кампаний. Максимум 50.
    """
    time.sleep(0.3)
    url = 'https://advert-api.wb.ru/adv/v1/promotion/adverts'
    payload = json.dumps(adv_list)
    response = requests.request("POST", url, headers=header, data=payload)
    return response


@api_retry_decorator
def advertisment_statistic_info(adv_list: list, header: str):
    """
    Статистика рекламной кампании ВБ за все время существования

    переменные:
    adv_list - список словарей рекламных кампаний вида:
        [
            {
                "id": 8960367,
                "interval": {
                    "begin": "2023-10-08",
                    "end": "2023-10-10"
                }
            }
        ]
    header - хедер для запроса

    Получаем данные из: https://advert-api.wb.ru/adv/v2/fullstats
    https://openapi.wb.ru/promotion/api/ru/#tag/Statistika/paths/~1adv~1v2~1fullstats/post

    Максимум 1 запрос в минуту.
    Данные вернутся для кампаний в статусе 7, 9 и 11.
    В списке максимум 100 элементов
    """
    time.sleep(60)
    url = 'https://advert-api.wb.ru/adv/v2/fullstats'
    payload = json.dumps(adv_list)
    response = requests.request("POST", url, headers=header, data=payload)
    print(response.status_code)
    return response


@api_retry_decorator
def advertisment_campaign_clusters_statistic(header, campaign_number):
    """
    Возвращает статистику по ключевым фразам за каждый день, когда кампания была активна.
    Информация обновляется раз в 15 минут.
    Максимум — 4 запроса секунду.
    """
    time.sleep(0.3)
    url = f'https://advert-api.wb.ru/adv/v2/auto/stat-words?id={campaign_number}'
    response = requests.request("GET", url, headers=header)
    print(campaign_number, response.status_code)
    return response


@api_retry_decorator
def statistic_search_campaign_keywords(header, campaign_number):
    """
    Статистика поисковой кампании по ключевым фразам.
    Метод позволяет получать статистику поисковой кампании по ключевым фразам.
    Допускается максимум 4 запроса в секунду.
    Информация обновляется примерно каждые полчаса.
    """
    time.sleep(0.3)
    url = f'https://advert-api.wb.ru/adv/v1/stat/words?id={campaign_number}'
    response = requests.request("GET", url, headers=header)
    print(campaign_number, response.status_code)
    return response


@api_retry_decorator
def statistic_catalog_search_campaign_with_keywords(header, campaign_number):
    """
    Статистика кампаний Поиск + Каталог.
    Метод позволяет получать статистику по кампаниям Поиск + Каталог.
    Допускается 2 запроса в секунду.
    """
    time.sleep(0.6)
    url = f'https://advert-api.wb.ru/adv/v1/seacat/stat?id={campaign_number}'
    response = requests.request("GET", url, headers=header)
    print(campaign_number, response.status_code)
    return response


@api_retry_decorator
def get_budget_adv_campaign(header, campaign_number):
    """
    Определяет бюджет рекламной кампании.
    Метод позволяет получать информацию о бюджете кампании.
    Допускается 4 запроса в секунду.
    """
    time.sleep(0.3)
    url = f'https://advert-api.wb.ru/adv/v1/budget?id={campaign_number}'
    response = requests.request("GET", url, headers=header)
    print(campaign_number, response.status_code)
    return response


# =========== РЕЙТИНГ И ОТЗЫВЫ ========== #
@api_retry_decorator
def average_rating_feedbacks_amount(header, wb_nmid):
    """
    Метод позволяет получить среднюю оценку товара по его артикулу WB.
    Допускается 1 запрос в секунду.

    Входящие переменные:
    wb_nmid - WB номенклатура артикула
    header - хедер для запроса
    """
    time.sleep(1)
    url = f'https://feedbacks-api.wb.ru/api/v1/feedbacks/products/rating/nmid?nmId={wb_nmid}'
    response = requests.request("GET", url, headers=header)
    return response
