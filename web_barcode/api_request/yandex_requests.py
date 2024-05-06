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
