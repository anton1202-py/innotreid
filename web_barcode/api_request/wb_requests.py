import json
import time
from datetime import datetime, timedelta

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



def get_article_list_data(header, limit=1000, offset=0, articles_data=None, counter=0):
    """
    Возвращает информацию о товаре по его артикулу.
    Чтобы получить информацию обо всех товарах, оставьте артикул пустым
    """
    if not articles_data:
        articles_data = []
    time.sleep(0.8)
    url = f'https://discounts-prices-api.wildberries.ru/api/v2/list/goods/filter?limit={limit}&offset={offset}'
    response = requests.request("GET", url, headers=header)
    if response.status_code == 200:
        main_data = json.loads(response.text)['data']['listGoods']
        for data in main_data:
            articles_data.append(data)
        if len(main_data) == limit:
            counter += 1
            offset = limit * counter
            return get_article_list_data(header, limit, offset, articles_data, counter)
        else:
            return articles_data


@api_retry_decorator
def get_front_api_wb_info(nm_id):
    """
    Получаем информацию артикула на странице ВБ от api фронта ВБ
    nm_id - номенклатурный номер артикула на WB
    """
    time.sleep(0.3)
    url = f'https://card.wb.ru/cards/detail?appType=0&curr=rub&dest=-446085&regions=80,83,38,4,64,33,68,70,30,40,86,75,69,1,66,110,22,48,31,71,112,114&spp=99&nm={nm_id}'
    response = requests.request(
        "GET", url)
    return response

# =========== API ЗАПРОСЫ ПРОДВИЖЕНИЯ WILDBERRIES ========== #


# @api_retry_decorator Не включать этот декоратор. На ответе response завязан вызывающий функцию код
def create_auto_advertisment_campaign(header, campaign_type, campaign_name, subject_id, budget, mns_list, cpm):
    """
    Создают автоматическую кампанию.
    Максимум 1 запрос в 20 секунд.

    type - Тип автоматической кампании: 8 (автоматическая).
    name - Название кампании (max. 128 символов).
    subjectId - ID предмета, для которого создается кампания.
    sum - Сумма пополнения
    btype - Tип списания (0 - Счёт, 1 - Баланс, 3 - Бонусы).
    on_pause - После создания кампания: 
        true - будет на паузе. Запуск кампании будет доступен через 3 минуты после создания кампании.
        false - будет сразу запущена
    nms - Массив артикулов WB. Максимум 100 артикулов.
    cpm - Ставка. Если будет указана ставка меньше допустимого размера, 
        то автоматически установится ставка минимально допустимого размера.
    header - хедер для запроса
    """
    time.sleep(21)
    url = 'https://advert-api.wb.ru/adv/v1/save-ad'
    print(
        "type", campaign_type,
        "name", campaign_name,
        "subjectId", subject_id,
        "sum", budget,
        "btype", 1,
        "on_pause", False,
        "nms", mns_list,
        "cpm", cpm
    )
    payload = json.dumps({
        "type": campaign_type,
        "name": campaign_name,
        "subjectId": subject_id,
        "sum": budget,
        "btype": 1,
        "on_pause": False,
        "nms": mns_list,
        "cpm": cpm
    })
    response = requests.request("POST", url, headers=header, data=payload)
    return response


@api_retry_decorator
def start_advertisment_campaigns(header, campaign_number):
    """
    Метод позволяет запускать кампании находящиеся в статусах 4 - готова к запуску или 11 - кампания на паузе.
    Допускается 5 запросов в секунду.
    Для запуска кампании со статусом 11 необходимо наличие у неё пополненного бюджета.

    Чтобы запустить кампанию со статусом 4 необходимо выполнить два условия (поочередность действий значения не имеет):
    1. После создания кампании в кабинете ВБ. Продвижение необходимо нажать кнопку "Применить изменения".
    2. Установить бюджет.
    """
    time.sleep(0.3)
    url = f'https://advert-api.wb.ru/adv/v0/start?id={campaign_number}'
    response = requests.request("GET", url, headers=header)
    return response


@api_retry_decorator
def replenish_deposit_campaigns(header, campaign_number, summ):
    """
    Метод позволяет пополнять бюджет кампании.
    Допускается 1 запрос в секунду.

    header - хедер для запроса
    campaign_number - номер рекламной кампании
    summ - суммадля пополнения
    """

    time.sleep(2)
    url = f'https://advert-api.wildberries.ru/adv/v1/budget/deposit?id={campaign_number}'
    payload = json.dumps({
        "sum": summ,
        "type": 1,
        "return": True
    })
    response = requests.request("POST", url, headers=header, data=payload)
    return response


@api_retry_decorator
def pausa_advertisment_campaigns(header, campaign_number):
    """
    Ставит на паузу рекламные кампании
    Допускается 5 запросов в секунду
    """
    time.sleep(0.3)
    url = f'https://advert-api.wb.ru/adv/v0/pause?id={campaign_number}'
    response = requests.request("GET", url, headers=header)
    return response


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
def get_del_minus_phrase_to_catalog_search_campaigns(header, campaign_number, phrase_list):
    """
    Установка/удаление минус-фраз фразового соответствия.

    Устанавливает и удаляет минус-фразы фразового соответствия.
    Только для кампаний в поиске и поиск + каталог.
    Максимально допустимое количество минус-фраз в кампании - 1000 шт.
    Отправка пустого массива удаляет все минус-фразы фразового соответствия из кампании.

    Максимум 2 запроса в секунду.
    """
    time.sleep(0.6)
    url = f'https://advert-api.wb.ru/adv/v1/search/set-phrase?id={campaign_number}'

    payload = json.dumps({
        "phrase": phrase_list
    })

    response = requests.request("POST", url, headers=header, data=payload)
    return response


# @api_retry_decorator
def get_del_minus_phrase_to_auto_campaigns(header, campaign_number, phrase_list):
    """
    Метод позволяет устанавливать или удалять минус фразы.

    Допускается 1 запрос в 6 секунд.
    Отправка пустого массива удаляет все минус-фразы из кампании.
    """
    time.sleep(10)
    url = f'https://advert-api.wb.ru/adv/v1/auto/set-excluded?id={campaign_number}'

    payload = json.dumps({
        "excluded": phrase_list
    })

    response = requests.request("POST", url, headers=header, data=payload)
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
def advertisment_balance_info(header: str, adv_number: int):
    """Получает информацию о рекламных кампаниях"""
    time.sleep(0.3)
    url = f'https://advert-api.wildberries.ru/adv/v1/budget?id={adv_number}'
    response = requests.request("GET", url, headers=header)
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
    time.sleep(65)
    url = 'https://advert-api.wb.ru/adv/v2/fullstats'
    payload = json.dumps(adv_list)
    response = requests.request("POST", url, headers=header, data=payload)
    return response


@api_retry_decorator
def advertisment_campaign_clusters_statistic(header, campaign_number):
    """
    Возвращает статистику по ключевым фразам за каждый день, когда кампания была активна.
    Информация обновляется раз в 15 минут.
    Максимум — 4 запроса секунду.
    """
    time.sleep(0.5)
    url = f'https://advert-api.wb.ru/adv/v2/auto/stat-words?id={campaign_number}'
    response = requests.request("GET", url, headers=header)
    return response


@api_retry_decorator
def statistic_search_campaign_keywords(header, campaign_number):
    """
    Статистика поисковой кампании по ключевым фразам.
    Метод позволяет получать статистику поисковой кампании по ключевым фразам.
    Допускается максимум 4 запроса в секунду.
    Информация обновляется примерно каждые полчаса.
    """
    time.sleep(0.5)
    url = f'https://advert-api.wb.ru/adv/v1/stat/words?id={campaign_number}'
    response = requests.request("GET", url, headers=header)
    return response


@api_retry_decorator
def statistic_keywords_auto_campaign(header, campaign_number):
    """
    Возвращает статистику по ключевым фразам за каждый день, когда кампания была активна.
    Информация обновляется раз в 15 минут.
    Максимум — 4 запроса секунду.
    """
    date_from = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
    date_to = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    time.sleep(0.5)
    url = f'https://advert-api.wildberries.ru/adv/v0/stats/keywords?advert_id={campaign_number}&from={date_from}&to={date_to}'
    response = requests.request("GET", url, headers=header)
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
    return response


@api_retry_decorator
def get_budget_adv_campaign(header, campaign_number):
    """
    Определяет бюджет рекламной кампании.
    Метод позволяет получать информацию о бюджете кампании.
    Допускается 4 запроса в секунду.
    """
    time.sleep(1)
    url = f'https://advert-api.wb.ru/adv/v1/budget?id={campaign_number}'
    response = requests.request("GET", url, headers=header)
    return response
# =========== КОНЕЦ API ЗАПРОСЫ ПРОДВИЖЕНИЯ WILDBERRIES ========== #

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


@api_retry_decorator
def average_rating_feedbacks_amount(header, wb_nmid):
    """
    Метод позволяет получить список отзывов с WB 
    по заданным параметрам с пагинацией и сортировкой.
    Допускается 1 запрос в секунду.

    Входящие переменные:
    wb_nmid - WB номенклатура артикула
    header - хедер для запроса
    """
    time.sleep(1)
    url = f'https://feedbacks-api.wildberries.ru/api/v1/feedbacks?nmId={wb_nmid}&isAnswered=true&take=5000&skip=0'
    response = requests.request("GET", url, headers=header)
    return response
# =========== КОНЕЦ БЛОКА РЕЙТИНГ И ОТЗЫВЫ ========== #


# =========== АКЦИИ ========== #
@api_retry_decorator
def wb_actions_first_list(header):
    """
    Возвращает список акций с датами и временем проведения
    Максимум 10 запросов за 6 секунд
    """
    time.sleep(1)
    start_date = datetime.now().strftime('%Y-%m-%d')
    finish_date = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
    url = f'https://dp-calendar-api.wildberries.ru/api/v1/calendar/promotions?allPromo=false&startDateTime={start_date}T00:00:00Z&endDateTime={finish_date}T23:59:59Z'
    response = requests.request("GET", url, headers=header)
    return response


@api_retry_decorator
def wb_action_details_info(header, action_ids_list):
    """
    Возвращает список акций с датами и временем проведения
    """
    time.sleep(1)
    url = f'https://dp-calendar-api.wildberries.ru/api/v1/calendar/promotions/details?{action_ids_list}'
    response = requests.request("GET", url, headers=header)
    return response


# @api_retry_decorator
def wb_articles_in_action(header, action_number, limit=1000, offset=0, counter=0, article_adv_data=None):
    """
    Возвращает список товаров, подходящих для участия в акции.
    Неприменимо для автоакций
    """
    time.sleep(1)
    if not article_adv_data:
        article_adv_data = []
    url = f'https://dp-calendar-api.wildberries.ru/api/v1/calendar/promotions/nomenclatures?promotionID={action_number}&inAction=false&limit={limit}&offset={offset}'
    response = requests.request("GET", url, headers=header)
    counter += 1
    if response.status_code == 200:
        articles_list = json.loads(response.text)['data']['nomenclatures']
        for data in articles_list:
                article_adv_data.append(data)
        if len(articles_list) == limit:
            offset = limit * counter
            return wb_articles_in_action(header, action_number, limit, offset, counter, article_adv_data)
        else:
            return article_adv_data
    else:
        return None



def add_wb_articles_to_action(header, action_number, wb_nom_list):
    """
    Создаёт загрузку товара в акцию.
    Состояние загрузки можно проверить с помощью отдельных методов.

    Неприменимо для автоакций
    """
    time.sleep(1)
    url = f'https://dp-calendar-api.wildberries.ru/api/v1/calendar/promotions/upload'
    payload = json.dumps({
        "data": {
            "promotionID": action_number,
            "uploadNow": True,
            "nomenclatures": wb_nom_list
        }
    })
    response = requests.request("POST", url, headers=header, data=payload)
    return response
    



# =========== КОНЕЦ АКЦИИ ========== #