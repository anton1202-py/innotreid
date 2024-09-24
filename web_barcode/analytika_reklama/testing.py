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

xlsx_file = 'D:/Projects/innotreid/web_barcode/analytika_reklama/Товары для акции_ЕЖЕВЫГОДА_ хиты супербуст_22.09.2024 14.03.45.xlsx'
def read_excel_file():
    excel_data_common = pd.read_excel(xlsx_file)
    sheet_names = pd.ExcelFile(xlsx_file).sheet_names
   
    df_info = pd.read_excel(xlsx_file)
    wb_article_dict = {}
    excel_data = pd.DataFrame(df_info, columns=[
                                  'Артикул WB'])
    article_list = excel_data['Артикул WB'].to_list()
    
    main_articles = Articles.objects.all()
    wb_tags_dict = {}
    for article in main_articles:
        wb_article_dict[article.wb_nomenclature] = article.wb_barcode
    
    for article in article_list:
        tags_id = []
        data = wb_request(wb_article_dict[article])
        if 'tags' in data:
            for tag in data['tags']:
                tags_id.append(tag['id'])
        wb_tags_dict[article] = tags_id
    
    for i, j in wb_tags_dict.items():
        if 1149658 not in j:
            j.append(1149658)
        
        wb_tags_work(i, j)
    
    
    print(wb_tags_dict)



def wb_request(barcode):
    time.sleep(0.7)
    api_url = 'https://content-api.wildberries.ru/content/v2/get/cards/list'

    payload = json.dumps(
        {
            "settings": {
               
                "filter": {
                    "textSearch": barcode,
                    "withPhoto": -1
                }
            }
        }
    )

    response = requests.request(
        "POST", api_url, headers=wb_data_ooo_headers, data=payload)

    if response.status_code == 200:
        all_data = json.loads(response.text)["cards"][0]
        return all_data


def wb_tags_work(nm_id, tag_list):
    time.sleep(0.7)
    api_url = 'https://content-api.wildberries.ru/content/v2/tag/nomenclature/link'
    payload = json.dumps(
        {
            "nmID": nm_id,
            "tagsIDs": tag_list
        }
    )
    response = requests.request(
        "POST", api_url, headers=wb_data_ooo_headers, data=payload)
    print(response.status_code)
