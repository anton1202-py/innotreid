import asyncio
import math
import time
from datetime import datetime, timedelta

from api_request.wb_requests import create_auto_advertisment_campaign
from create_reklama.models import CreatedCampaign
from django.db.models import Q
from motivation.models import Selling
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg
from reklama.models import UrLico

from web_barcode.constants_file import CHAT_ID_ADMIN, bot, header_wb_dict


def check_data_for_create_adv_campaign(main_data):
    """Обрабатывает и проверяет данные для создания рекламной кампании"""

    raw_articles = main_data['articles']
    ur_lico = UrLico.objects.get(id=main_data['ur_lico'])
    ur_lico_name = ur_lico.ur_lice_name
    campaign_type = int(main_data['select_type'])
    subject_id = int(main_data['select_subject'])
    cpm = int(main_data['cpm'])
    budget = int(main_data['budget'])
    # user_chat_id = int(main_data['user_chat_id'])

    header = header_wb_dict[ur_lico_name]
    result_articles = raw_articles.split(', ')

    mns_list = []
    main_articles_list = Articles.objects.filter(
        company=ur_lico).values('wb_nomenclature')
    articles_list = []
    for article in main_articles_list:
        articles_list.append(str(article['wb_nomenclature']))

    # Проверка артикулов на наличие в системе:
    for nmid in result_articles:
        if nmid not in articles_list:
            error = f'Нет артикула {nmid} в на портале у {ur_lico}.'
            # bot.send_message(chat_id=user_chat_id,
            #                  text=error[:4000])
        else:
            mns_list.append(int(nmid))

    for nm_id in mns_list:
        message1 = f'Я перед ожиданием слип 21'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message1[:4000])
        time.sleep(10)
        message1 = f'Я после ожиданием слип 21'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message1[:4000])
        nm_id_for_request = [nm_id]
        article_name = Articles.objects.filter(
            company=ur_lico, wb_nomenclature=nm_id)[0].name
        name_for_request = f'{nm_id} {article_name}'
        message1 = f'Создаю кампанию для {name_for_request}'
        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=message1[:4000])
        # time.sleep(10)
        # response = create_auto_advertisment_campaign(
        #     header, campaign_type, name_for_request, subject_id, budget, nm_id_for_request, cpm)

        # bot.send_message(chat_id=CHAT_ID_ADMIN,
        #                  text=f'ответ на создание кампании {name_for_request} {response.text}')

        # if response.status_code != 200:
        #     error = f'Не создал кампанию для артикула {nm_id} ({article_name}). Ошибка: {response.text}'
        #     bot.send_message(chat_id=user_chat_id,
        #                      text=error[:4000])
        # else:
        #     error = f'Создал кампанию для артикула {nm_id} ({article_name}). Ее номер: {response.text}'
        #     bot.send_message(chat_id=user_chat_id,
        #                      text=error[:4000])
        # saved_data = {
        #     'ur_lico': UrLico.objects.get(id=main_data['ur_lico']),
        #     'campaign_name': name_for_request,
        #     'campaign_number': int(response.text),
        #     'campaign_type': int(main_data['select_type']),
        #     'subject_id': int(main_data['select_subject']),
        #     'cpm': int(main_data['cpm']),
        #     'budget': int(main_data['budget']),
        #     'article': nm_id
        # }
        # message1 = 'Создал кампанию и нужно ее сохранить'
        # bot.send_message(chat_id=CHAT_ID_ADMIN,
        #                  text=message1[:4000])
        # try:
        # add_created_campaign_data_to_database(saved_data)
        # except:
        #     error = f'Ошибка в функции add_created_campaign_data_to_database'
        #     bot.send_message(chat_id=user_chat_id,
        #                      text=error[:4000])


@sender_error_to_tg
def add_created_campaign_data_to_database(main_data):
    """Обрабатывает и проверяет данные для создания рекламной кампании"""

    article = main_data['article']
    ur_lico = main_data['ur_lico']
    campaign_number = main_data['campaign_number']
    campaign_type = main_data['campaign_type']
    campaign_name = main_data['campaign_name']
    subject_id = int(main_data['subject_id'])

    cpm = main_data['cpm']
    budget = main_data['budget']
    today = datetime.now().strftime("%Y-%m-%d %H:%M")

    CreatedCampaign(
        ur_lico=ur_lico,
        campaign_name=campaign_name,
        campaign_number=campaign_number,
        campaign_type=campaign_type,
        campaign_status=9,
        create_date=today,
        articles_name=article,
        subject_id=subject_id,
        current_cpm=cpm
    ).save()
