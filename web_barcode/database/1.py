import requests
import json
import pandas as pd


data_file = r'web_barcode\database\2023_08_10_yandex_sku.xlsx'
excel_data = pd.read_excel(data_file)
data = pd.DataFrame(
            excel_data, columns=['Ваш SKU'])

article_list = data['Ваш SKU'].to_list()
url = "https://api.partner.market.yandex.ru/campaigns/42494921/stats/skus"

headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer y0_AgAEA7qjt7KxAApPWwAAAADpxzharlAhWWWhR-CN6aC7F0W9cZImPgo',
  'Cookie': '_yasc=0pnD6PcW7xKIeoHhn1cC8dXbLz8mZL4kfI3BdNrRo5LQsXYW0qa+OvGuRwKRRtM=; i=rCGjEcoavotQC8BusElWmTIvxgUDMWQxQYgBUJSkh0SZnNVS3noWuJVqx//ZgXQtL7wHkrdun3HUWMvcJmIgqug1wZk=; yandexuid=4089427681691529915'
}
rand_list=article_list
m = len(rand_list)%400 # остаток
n = len(rand_list)//400

fby_common_data_storage = {}
x = 0
for i in range(1):
    start = i*400
    finish = (i+1)*400
    new_list = rand_list[start:finish]

    payload = json.dumps({"shopSkus": new_list})

    response = requests.request("POST", url, headers=headers, data=payload)
    data = json.loads(response.text)
    result = data['result']
    dict_res = result['shopSkus']
    for res in dict_res:
        stocks_data = res['warehouses']
        stock_article = res['shopSku']
        #print(stock_article, stocks_data)
        stocks = stocks_data[0]
        if len(stocks['stocks']) > 0:
            for sum in stocks['stocks']:
                if sum['type'] == 'AVAILABLE':
                    fby_common_data_storage[stock_article] = sum['count']
        else:
            fby_common_data_storage[stock_article] = 0
#for i in fby_common_data_storage.items():
#    print(i)