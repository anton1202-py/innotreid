import asyncio
import math
import pprint
import time
from datetime import datetime, timedelta

from api_request.wb_requests import (advertisment_campaign_list,
                                     advertisment_campaigns_list_info,
                                     create_auto_advertisment_campaign,
                                     get_budget_adv_campaign,
                                     get_front_api_wb_info)
from create_reklama.models import CreatedCampaign
from django.db.models import Q
from motivation.models import Selling
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg
from reklama.models import AdvertisingCampaign, ProcentForAd, UrLico

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
    user_chat_id = int(main_data['user_chat_id'])

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
            bot.send_message(chat_id=user_chat_id,
                             text=error[:4000])
        else:
            mns_list.append(int(nmid))

    for nm_id in mns_list:
        nm_id_for_request = [nm_id]
        article_name = Articles.objects.filter(
            company=ur_lico, wb_nomenclature=nm_id)[0].name
        name_for_request = f'{nm_id} {article_name}'

        response = create_auto_advertisment_campaign(
            header, campaign_type, name_for_request, subject_id, budget, nm_id_for_request, cpm)

        bot.send_message(chat_id=CHAT_ID_ADMIN,
                         text=f'ответ на создание кампании {name_for_request} {response.text}')

        if response.status_code != 200:
            error = f'Не создал кампанию для артикула {nm_id} ({article_name}). Ошибка: {response.text}'
            bot.send_message(chat_id=user_chat_id,
                             text=error[:4000])
        else:
            error = f'Создал кампанию для артикула {nm_id} ({article_name}). Ее номер: {response.text}'
            bot.send_message(chat_id=user_chat_id,
                             text=error[:4000])
        saved_data = {
            'ur_lico': UrLico.objects.get(id=main_data['ur_lico']),
            'campaign_name': name_for_request,
            'campaign_number': int(response.text),
            'campaign_type': int(main_data['select_type']),
            'subject_id': int(main_data['select_subject']),
            'cpm': int(main_data['cpm']),
            'budget': int(main_data['budget']),
            'article': nm_id
        }

        add_created_campaign_data_to_database(saved_data)
        save_campaign_for_replenish_budget(saved_data)


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


@sender_error_to_tg
def save_campaign_for_replenish_budget(main_data):
    """Сохраняет кампанию в таблицу для пополнения бюджета"""

    ur_lico = main_data['ur_lico']
    campaign_number = main_data['campaign_number']
    campaign_type = main_data['campaign_type']
    campaign_name = main_data['campaign_name']
    subject_id = int(main_data['subject_id'])

    cpm = main_data['cpm']
    budget = main_data['budget']
    today = datetime.now().strftime("%Y-%m-%d %H:%M")

    AdvertisingCampaign(
        campaign_number=campaign_number,
        ur_lico=ur_lico,
        create_date=today
    ).save()
    adv_obj = AdvertisingCampaign.objects.filter(
        ur_lico=ur_lico, campaign_number=campaign_number)[0]
    ProcentForAd(
        campaign_number=adv_obj,
        koefficient=4,
        koef_date=today,
        virtual_budget=0,
        virtual_budget_date=today,
        campaign_budget_date=today
    ).save()


def filter_campaigns_status_type() -> dict:
    """
    Фильтрует рекламные кампании по статусу и типу.
    Возвращает словарь типа:
    {ur_lico:
        {campaign_type:
            {campaign_status: [campaign_number]}
        }
    }
    """
    ur_lico_data = UrLico.objects.all()
    returned_dict = {}
    type_list = [8, 9]
    for ur_lico_obj in ur_lico_data:
        header = header_wb_dict[ur_lico_obj.ur_lice_name]
        campaigns_wb_answer_list = advertisment_campaign_list(header)
        inner_campaigns_data = {}
        for data in campaigns_wb_answer_list['adverts']:

            # Автоматические кампании
            if data['type'] in type_list:

                if data['type'] in inner_campaigns_data:
                    inner_campaign_list = []
                    for campaign in data['advert_list']:
                        inner_campaign_list.append(campaign['advertId'])
                    inner_campaigns_data[data['type']
                                         ][data['status']] = inner_campaign_list
                else:
                    inner_campaign_list = []
                    for campaign in data['advert_list']:
                        inner_campaign_list.append(campaign['advertId'])
                    inner_campaigns_data[data['type']] = {
                        data['status']: inner_campaign_list}
        returned_dict[ur_lico_obj.ur_lice_name] = inner_campaigns_data
    return returned_dict


def update_campaign_budget_and_cpm():
    """
    Обновляет данные кампании (бюджет и cpm)
    """
    ur_lico_data = UrLico.objects.all()

    for ur_lico_obj in ur_lico_data:
        campaigns_list = []
        header = header_wb_dict[ur_lico_obj.ur_lice_name]
        campaign_queryset = CreatedCampaign.objects.filter(ur_lico=ur_lico_obj)
        for campaign_obj in campaign_queryset:
            update_campaign_budget(campaign_obj, header)
            campaigns_list.append(int(campaign_obj.campaign_number))

        check_number = math.ceil(len(campaigns_list)/50)

        for i in range(check_number):
            start_point = i*50
            finish_point = (i+1)*50
            data_adv_list = campaigns_list[
                start_point:finish_point]
            update_campaign_cpm(data_adv_list, ur_lico_obj, header)


def update_campaign_cpm(data_adv_list, ur_lico_obj, header):
    """
    Обновляет cpm кампании
    """
    main_data = advertisment_campaigns_list_info(data_adv_list, header)
    for campaign_data in main_data:
        if "autoParams" in campaign_data:
            if 'cpm' in campaign_data["autoParams"]:
                cpm = campaign_data["autoParams"]['cpm']
            else:
                cpm = None
        else:
            cpm = None
        campaign_obj = CreatedCampaign.objects.get(
            ur_lico=ur_lico_obj, campaign_number=str(campaign_data["advertId"]))
        campaign_obj.current_cpm = cpm
        campaign_obj.save()


def update_campaign_budget(campaign_obj, header):
    """
    Обновляет бюджет кампании
    """
    budget_data = get_budget_adv_campaign(
        header, int(campaign_obj.campaign_number))
    if budget_data:
        balance = budget_data['total']
        campaign_obj.balance = balance
        campaign_obj.save()
