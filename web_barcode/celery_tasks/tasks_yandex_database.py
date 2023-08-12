import json
import os
from datetime import datetime, timedelta

import pandas as pd
import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv()

# Адрес, где лежит файл с артикулами
ARTICLE_DATA_FILE = r'web_barcode\database\2023_08_10_yandex_sku.xlsx'
# Эндпоинт для информации по количеству товара на складе FBY
URL_FBY = f"https://api.partner.market.yandex.ru/campaigns/{os.getenv('FBY_COMPAIGNID')}/stats/skus"
# Эндпоинт для изменения остатков на складе FBS
URL_FBS = f"https://api.partner.market.yandex.ru/campaigns/{os.getenv('FBS_COMPAIGNID')}/offers/stocks"

headers = {
  'Content-Type': 'application/json',
  'Authorization': os.getenv('API_KEY_YANDEX')
}


excel_data = pd.read_excel(ARTICLE_DATA_FILE)
data = pd.DataFrame(excel_data, columns=['Ваш SKU'])
article_list = data['Ваш SKU'].to_list()
# ограничения по передачи количества артикулов в одном запросе - 500 штук. 
residue = len(article_list) % 400 # остаток
iter_amount = len(article_list) // 400
# Словарь для данных по артикулу и его остатку на складе, если он != 0.
fby_common_data_storage = {}
for i in range(iter_amount+1):
    start_point = i*400
    finish_point = (i+1)*400
    articke_info_list = article_list[start_point:finish_point]
    # ПОСТ запрос для получения данных по артикулу
    payload = json.dumps({"shopSkus": articke_info_list})
    response = requests.request("POST", URL_FBY, headers=headers, data=payload)

    data = json.loads(response.text)
    result = data['result']
    dict_res = result['shopSkus']
    for res in dict_res:
    
        stocks_data = res['warehouses']
        stock_article = res['shopSku']
        for j in stocks_data:
            if len(j['stocks'])>0:
                for sum in j['stocks']:
                    if sum['type'] == 'AVAILABLE':
                        fby_common_data_storage[stock_article] = sum['count']
print(fby_common_data_storage)
