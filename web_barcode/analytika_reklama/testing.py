from datetime import datetime
import json
import os
import time
import zipfile
import tarfile

import pandas as pd
import requests
from web_barcode.constants_file import wb_data_ooo_headers
from price_system.models import Articles


def read_excel_file():
    
    wb_tags_dict = wb_article_data_from_api(wb_data_ooo_headers)
    
    print(wb_tags_dict)
    for i, j in wb_tags_dict.items():
        wb_tags_work(i, j)
    
    
    




def wb_article_data_from_api(wb_data_ooo_headers, update_date=None, mn_id=0, common_data=None, counter=0):
    """Получаем данные всех артикулов в ВБ"""
    if not common_data:
        common_data = {}
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
        "POST", url, headers=wb_data_ooo_headers, data=payload)

    counter += 1
    if response.status_code == 200:
        all_data = json.loads(response.text)["cards"]
        check_amount = json.loads(response.text)['cursor']
        for data in all_data:
            tags_id = []
            if 'tags' in data:
                for tag in data['tags']:
                    if tag['id'] == 1149658:
                        tags_id.append(tag['id'])
                        common_data[data['nmID']] = tags_id
        if len(json.loads(response.text)["cards"]) == 100:
            # time.sleep(1)
            return wb_article_data_from_api(wb_data_ooo_headers,
                                            check_amount['updatedAt'], check_amount['nmID'], common_data, counter)
        return common_data
    elif response.status_code != 200 and counter <= 50:
        return wb_article_data_from_api(wb_data_ooo_headers, update_date, mn_id, common_data, counter)


def wb_tags_work(nm_id, tag_list):
    time.sleep(0.7)
    # api_url = 'https://content-api.wildberries.ru/content/v2/tag/nomenclature/link'
    # payload = json.dumps(
    #     {
    #         "nmID": nm_id,
    #         "tagsIDs": tag_list
    #     }
    # )
    # response = requests.request(
    #     "POST", api_url, headers=wb_data_ooo_headers, data=payload)
    # print(response.status_code)
