import io
import os
from contextlib import closing
from datetime import datetime

import dropbox
import img2pdf
import pandas as pd
from barcode import Code128
from barcode.writer import ImageWriter
from dotenv import load_dotenv
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont

version = 'w1.0'

dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)

REFRESH_TOKEN_DB = os.getenv('REFRESH_TOKEN_DB')
APP_KEY_DB = os.getenv('APP_KEY_DB')
APP_SECRET_DB = os.getenv('APP_SECRET_DB')
API_KEY_WB_IP = os.getenv('API_KEY_WB_IP')

dbx_db = dropbox.Dropbox(oauth2_refresh_token=REFRESH_TOKEN_DB,
                         app_key=APP_KEY_DB,
                         app_secret=APP_SECRET_DB)


def stream_dropbox_file(path):
    _, res = dbx_db.files_download(path)
    with closing(res) as result:
        byte_data = result.content
        return io.BytesIO(byte_data)


dict_barcode_print = {'S296': ['название светильника', 1234567891234], 'S287': [
    'название светильника', 1234567891244]}


def common_barcode_design(dict_barcode_print):
    """
    dict_barcode_print - словарь с данными для штрихкода {артикул: [название светильника, штрихкод]}
    """

    UR_LICO_DATA = '/DATABASE/web_barcode_data/helper_files/Печать Караваев.xlsx'
    ur_lico_data = stream_dropbox_file(UR_LICO_DATA)

    df = pd.read_excel(ur_lico_data, header=None)
    value_a1 = df.iloc[0, 0]  # значение ячейки A1
    value_a2 = df.iloc[1, 0]  # значение ячейки A2
    value_a3 = df.iloc[2, 0]  # значение ячейки A3
    value_a4 = df.iloc[3, 0]  # значение ячейки A4
    value_a5 = df.iloc[4, 0]  # значение ячейки A5
    value_a6 = df.iloc[5, 0]  # значение ячейки A6

    # Задаем размер штрихкода
    barcode_size = [img2pdf.in_to_pt(2.759), img2pdf.in_to_pt(1.95)]
    layout_function = img2pdf.get_layout_fun(barcode_size)

    font = ImageFont.truetype("arial.ttf", size=50)
    font2 = ImageFont.truetype("arial.ttf", size=60)
    font3 = ImageFont.truetype("arial.ttf", size=120)
    font_version = ImageFont.truetype("arial.ttf", size=35)

    current_date = datetime.now().strftime("%d.%m.%Y")
    EAC_FILE = '/DATABASE/web_barcode_data/programm_data/eac.png'

    metadata, response = dbx_db.files_download(EAC_FILE)
    if not os.path.exists('web_barcode/fbs_mode/data_for_barcodes/cache_dir/'):
        os.makedirs('web_barcode/fbs_mode/data_for_barcodes/cache_dir/')
    with open('web_barcode/fbs_mode/data_for_barcodes/eac.png', 'wb') as eac_file:
        eac_file.write(response.content)

        # Создание самого штрихкода
    for key, value in dict_barcode_print.items():
        render_options = {
            "module_width": 1,
            "module_height": 35,
            "font_size": 20,
            "text_distance": 8,
            "quiet_zone": 8
        }
        barcode = Code128(
            f'{str(value[1])[:13]}',
            writer=ImageWriter()
        ).render(render_options)
        im = Image.new('RGB', (1980, 1400), color=('#000000'))
        image1 = Image.open('web_barcode/fbs_mode/data_for_barcodes/eac.png')
        draw_text = ImageDraw.Draw(im)
        # Длина подложки
        w_width = round(im.width/2)
        # Длина штрихкода
        w = round(barcode.width/2)
        # Расположение штрихкода по центру
        position = w_width - w
        # Вставляем штрихкод в основной фон
        im.paste(barcode, ((w_width - w), 250))
        # Вставляем EAC в основной фон
        im.paste(image1, (1505, 1028))
        draw_text.text(
            (position, 150),
            f'{value[0]}\n',
            font=font2,
            fill=('#ffffff'), stroke_width=1
        )
        draw_text.text(
            (position, barcode.height+270),
            f'{key}\n',
            font=font3,
            fill=('#ffffff'), stroke_width=1
        )
        draw_text.text(
            (position, barcode.height+410),
            f'{value_a1}\n'
            f'{value_a2}{current_date}\n'
            f'{value_a3} {value_a4}\n'
            f'{value_a5}\n'
            f'{value_a6}',
            font=font,
            fill=('#ffffff')
        )
        draw_text.text(
            (1780, 70),
            version,
            font=font_version,
            fill=('#ffffff')
        )
        im.save(f'web_barcode/fbs_mode/data_for_barcodes/cache_dir/{key}.png')
        im.close()
        pdf = img2pdf.convert(
            f'web_barcode/fbs_mode/data_for_barcodes/cache_dir/{key}.png',
            layout_fun=layout_function)
        with open(f'web_barcode/fbs_mode/data_for_barcodes/cache_dir/{key}.pdf', 'wb') as f:
            f.write(pdf)


common_barcode_design(dict_barcode_print)
