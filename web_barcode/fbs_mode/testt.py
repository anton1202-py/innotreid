import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import yagmail

from web_barcode.constants_file import (CHAT_ID_ADMIN, CHAT_ID_AN, CHAT_ID_EU,
                                        CHAT_ID_MANAGER, EMAIL_ADDRESS_FROM,
                                        EMAIL_ADDRESS_FROM_PASSWORD,
                                        EMAIL_ADDRESS_TO, POST_PORT,
                                        POST_SERVER, bot, dbx_db,
                                        header_wb_dict, wb_headers_karavaev,
                                        wb_headers_ooo)


def send_email_test():
    # Настройки
    smtp_server = POST_SERVER  # Замените на SMTP-сервер вашего провайдера
    smtp_port = POST_PORT  # Обычно 587 для TLS
    username = EMAIL_ADDRESS_FROM
    password = EMAIL_ADDRESS_FROM_PASSWORD
    from_email = EMAIL_ADDRESS_FROM
    to_email = EMAIL_ADDRESS_TO
    subject = 'Сборка'
    body = 'Текст вашего письма'
    yag = yagmail.SMTP(from_email, password)
    # Создаем сообщение
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Добавляем текст в сообщение
    msg.attach(MIMEText(body, 'plain'))

    filename = 'fbs_mode/data_for_barcodes/pivot_excel/sdfsdfsdf.xlsx'

    try:
        # Открываем файл в бинарном режиме
        with open(filename, 'rb') as attachment:
            # Создаем вложение
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                            f'attachment; filename*=UTF-8\'\'{filename}')

            # Добавляем вложение в сообщение
            msg.attach(part)
    except Exception as e:
        print(f'Не удалось прикрепить файл {filename}: {e}')

    # Отправляем письмо
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Начинаем TLS шифрование
        server.login(username, password)
        server.send_message(msg)
        print('Письмо успешно отправлено')
    except Exception as e:
        print(f'Ошибка: {e}')
    finally:
        server.quit()
