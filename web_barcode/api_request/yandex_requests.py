import json
from datetime import datetime

import requests

from web_barcode.constants_file import CHAT_ID_ADMIN, bot


# Create your tests here.
def fbs_warehouse_article_balance(article, warehouse_id, amount, header, fbs_campaign_id):
    """
    Обновляет баланс на складе FBS в Яндекс Маркете
    article - арткул продавца (SKU) для обновления
    warehouse_id - ID склада для обновления
    amount - количество товара, которое должно стать на складе warehouse_id
    header - header юр лица для запроса
    """
    update_balance_url = f'https://api.partner.market.yandex.ru/campaigns/{fbs_campaign_id}/offers/stocks'
    time_now = datetime.now()
    now = time_now.strftime('%Y-%m-%dT%H:%M:%S+03:00')

    # Обновляем остатки на FBS
    payload = json.dumps({
        "skus": [
            {
                "sku": article,
                "warehouseId": warehouse_id,
                "items": [
                    {
                        "count": amount,
                        "type": "FIT",
                        "updatedAt": now
                    }
                ]
            }
        ]
    })
    response = requests.request(
        "PUT", update_balance_url, headers=header, data=payload)
    if response.status_code != 200:
        message = f'Статус код {response.status_code} для обновления остатка на ФБС складе ЯНдекс маркета. Для артикула {article}'
        bot.send_message(chat_id=CHAT_ID_ADMIN, text=message)


def yandex_daily_orders(header, campaign_id, order_date, counter=0):
    """
    Получает ежедневные доставленные заказы с Яндекс Маркета
    header - Хедер юр лица для запроса к АПИ
    campaign_id - Идентификатор кампании в API и магазина в кабинете
    order_date - Дата, за которую нужно получить заказ
    """
    url = f"https://api.partner.market.yandex.ru/campaigns/{campaign_id}/stats/orders?limit=200"
    counter += 1
    payload = json.dumps({
        "dateFrom": order_date,
        "dateTo": order_date,
        "orders": [],
        "statuses": [
            "DELIVERED"
        ],
        "hasCis": False
    })

    response = requests.request("POST", url, headers=header, data=payload)
    if response.status_code == 200:
        return json.loads(response.text)
    elif response.status_code != 200 and counter <= 50:
        return yandex_daily_orders(header, campaign_id, order_date, counter)
    else:
        message = f'Статус код {response.status_code} api_request.yandex_daily_orders'
        bot.send_message(chat_id=CHAT_ID_ADMIN, text=message)
