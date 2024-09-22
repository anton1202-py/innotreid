from datetime import datetime
import os
import zipfile
import tarfile

import pandas as pd

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
    ozon_sku_list = []
    for article in main_articles:
        wb_article_dict[article.wb_nomenclature] = article.ozon_sku
    
    for i in article_list:
        ozon_sku_list.append(wb_article_dict[i])
    print(ozon_sku_list)




read_excel_file()