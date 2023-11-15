import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()


url = "https://performance.ozon.ru/api/client/campaign?state=CAMPAIGN_STATE_RUNNING"

payload = json.dumps({
    "filter": {
        "operation_type": [],
        "posting_number": "",
        "transaction_type": "all"
    },
    "page": 1,
    "page_size": 1000
})
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {os.getenv("BEARER_TOKEN")}',
}
response = requests.request("GET", url, headers=headers, data=payload)
print(response)
compaign_data = json.loads(response.text)['list']

for i in compaign_data:
    print(i)
    print('****************')
