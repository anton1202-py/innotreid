from datetime import date, datetime, timedelta
import glob
import pandas as pd


import pandas


df = pd.read_excel('../innotreid/web_barcode/database/test.xlsx')
print(df)
# print whole sheet data



myfile = '../innotreid/web_barcode/database/test.xlsx'
empexceldata = pd.read_excel(myfile)
load_excel_data_wb_stock = pd.DataFrame(
    empexceldata, columns=['Общий артикул', 'Наш Артикул на WB (артикул поставщика)',
                           'Barcode WB', 'Артикул WB (номенклатура)',
                           'Наш Артикул на OZON (артикул поставщика)',
                           'OZON Product ID', 'FBO OZON SKU ID',
                           'FBS OZON SKU ID', 'Barcode OZON',
                           'Наш Артикул на Яндекс (артикул поставщика)',
                           'Barcode YANDEX', 'SKU на YANDEX'])
common_article_list = load_excel_data_wb_stock['Общий артикул'].to_list()
article_seller_wb_list = load_excel_data_wb_stock['Наш Артикул на WB (артикул поставщика)'].to_list()
article_wb_nomenclature_list = load_excel_data_wb_stock['Артикул WB (номенклатура)'].to_list()
barcode_wb_list = load_excel_data_wb_stock['Barcode WB'].to_list()
article_seller_ozon_list = load_excel_data_wb_stock['Наш Артикул на OZON (артикул поставщика)'].to_list()
ozon_product_id_list = load_excel_data_wb_stock['OZON Product ID'].to_list()
fbo_ozon_sku_id_list = load_excel_data_wb_stock['FBO OZON SKU ID'].to_list()
fbs_ozon_sku_id_list = load_excel_data_wb_stock['FBS OZON SKU ID'].to_list()
barcode_ozon_list = load_excel_data_wb_stock['Barcode OZON'].to_list()
article_seller_yandex_list = load_excel_data_wb_stock['Наш Артикул на Яндекс (артикул поставщика)'].to_list()
barcode_yandex_list = load_excel_data_wb_stock['Barcode YANDEX'].to_list()
sku_yandex_list = load_excel_data_wb_stock['SKU на YANDEX'].to_list()
dbframe = empexceldata

for i in ozon_product_id_list:
    print(type(i), i)
print(ozon_product_id_list)