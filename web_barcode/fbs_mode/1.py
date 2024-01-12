import base64
import glob
import io
import json
import math
import os
import shutil
import time
from collections import Counter
from contextlib import closing
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

import dropbox
import img2pdf
import openpyxl
import pandas as pd
import psycopg2
import pythoncom
import requests
import win32com.client as win32
from barcode import Code128
from barcode.writer import ImageWriter
from dotenv import load_dotenv
from helpers import (merge_barcode_for_ozon_two_on_two,
                     new_data_for_ozon_ticket, print_barcode_to_pdf2,
                     qrcode_print_for_products, special_design_dark,
                     special_design_light, supply_qrcode_to_standart_view)
from openpyxl import Workbook, load_workbook
from openpyxl.drawing import image
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from PIL import Image, ImageDraw, ImageFont
from PyPDF3 import PdfFileReader, PdfFileWriter
from PyPDF3.pdf import PageObject
from sqlalchemy import create_engine
from win32com.client import DispatchEx

amount_articles = {'V109-b': 1, 'V142-b': 2, 'V305-b': 4, 'V545': 1}
ozon_article_amount = {'L011-b': 2, 'V109-b': 2, 'V267-b': 1, 'V360-b': 8,
                       'V426-b': 1, 'V457-b': 1, 'V517': 1, 'V545': 2, 'V547': 1, 'V551': 1}


# Задаем словарь с данными WB, а входящий становится общим для всех маркетплейсов
wb_article_amount = amount_articles.copy()
hour = datetime.now().hour
date_folder = datetime.today().strftime('%Y-%m-%d')

for article in ozon_article_amount.keys():
    if article in amount_articles.keys():
        amount_articles[article] = int(
            amount_articles[article]) + int(ozon_article_amount[article])
    else:
        amount_articles[article] = int(
            ozon_article_amount[article])
sorted_data_for_pivot_xls = dict(
    sorted(amount_articles.items(), key=lambda v: v[0].upper()))

print(sorted_data_for_pivot_xls)
print(wb_article_amount)
