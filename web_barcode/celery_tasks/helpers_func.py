import io
import os
import traceback
from contextlib import closing

import dropbox
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)


REFRESH_TOKEN_DB = os.getenv('REFRESH_TOKEN_DB')
APP_KEY_DB = os.getenv('APP_KEY_DB')
APP_SECRET_DB = os.getenv('APP_SECRET_DB')

dbx_db = dropbox.Dropbox(oauth2_refresh_token=REFRESH_TOKEN_DB,
                         app_key=APP_KEY_DB,
                         app_secret=APP_SECRET_DB)


def error_message(function_name: str, function, error_text: str) -> str:
    """
    Формирует текст ошибки и выводит информацию в модальном окне
    function_name - название функции.
    function - сама функция, как объект, а не результат работы. Без скобок.
    error_text - текст ошибки.
    """
    tb_str = traceback.format_exc()
    message_error = (f'Ошибка в функции: <b>{function_name}</b>\n'
                     f'<b>Функция выполняет</b>: {function.__doc__}\n'
                     f'<b>Ошибка</b>\n: {error_text}\n\n'
                     f'<b>Техническая информация</b>:\n {tb_str}')
    return message_error


def stream_dropbox_file(path):
    """
    Открывает файл по ссылке на Dropbox
    path - ссыдка на файл на dropbox
    """
    _, res = dbx_db.files_download(path)
    with closing(res) as result:
        byte_data = result.content
        return io.BytesIO(byte_data)
