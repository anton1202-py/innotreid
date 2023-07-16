import requests
import json
import sqlite3
from contextlib import closing
import io
import os
import os.path
import psutil 
import pandas as pd
import PySimpleGUI as sg
from datetime import date,  timedelta
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import dropbox



refresh_token_db = 'kcjuYCMJ958AAAAAAAAAAbSglZkCTY50p7ksrTLt2e5d7zJM5_uf1D6URbTOwgQJ'
app_key_db = '3rvhk6f0pjdksc8'
app_secret_db = '3a1pe948esjx39d'
dbx_db = dropbox.Dropbox(oauth2_refresh_token=refresh_token_db,
                      app_key=app_key_db,
                      app_secret=app_secret_db)


def stream_dropbox_file(path):
        _,res=dbx_db.files_download(path)
        with closing(res) as result:
            byte_data=result.content
            return io.BytesIO(byte_data)
        
path = '/DATABASE/Ночники ИП.xlsx'
main_file = stream_dropbox_file(path)
main_file_location = main_file
excel_data = pd.read_excel(main_file_location)
data = pd.DataFrame(
    excel_data, columns=['Артикул продавца', 'Баркод товара', 'Наименование'])
barcodes_for_print_raw = data['Баркод товара'].to_list()

new_barcode = []

for i in barcodes_for_print_raw:
      new_barcode.append(f"{i}")

control_date_stock = date.today() - timedelta(days=1)
control_date_sales = date.today() - timedelta(days=1)
url_warehouse = "https://suppliers-api.wildberries.ru/api/v3/warehouses"
url_stock = f"https://feedbacks-api.wildberries.ru/api/v1/feedbacks"
#url_sales = f"https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom={control_date_sales}&flag=1"
               
# Заголовок и сам ключ
payload = json.dumps({
  "skus": new_barcode
})
headers = {
  'Content-Type': 'application/json',
  'Authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NJRCI6ImYzOWQ1NWMzLTY2YWYtNDA5OC1iNTgyLTBmMDExZjUxNDljMSJ9.vXvxsCxIoLUZSUp0110whzs8wgN1JJbr6ZmHRyI25Tc'
}
APIKEY = {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NJRCI6ImYzOWQ1NWMzLTY2YWYtNDA5OC1iNTgyLTBmMDExZjUxNDljMSJ9.vXvxsCxIoLUZSUp0110whzs8wgN1JJbr6ZmHRyI25Tc"}
response = requests.request("GET", url_stock, headers=headers, data=payload)
print(response.text)


response_ware = requests.get(url_warehouse, headers=APIKEY)
data_house = json.loads(response_ware.text) 

