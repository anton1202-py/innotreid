from dotenv import load_dotenv
import os
import requests
import json
# Загрузка переменных окружения из файла .env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)

# Использование переменных окружения
API_KEY_WB_IP = os.getenv('API_KEY_WB_IP')



url = "https://suppliers-api.wildberries.ru/api/v3/orders/new"

payload = {}
headers = {
    'Authorization': API_KEY_WB_IP
}

response = requests.request("GET", url, headers=headers, data=payload)
orders_data = json.loads(response.text)['orders']
for order in orders_data:
    print(order)
