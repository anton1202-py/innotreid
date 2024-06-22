import math
import time
from datetime import datetime, timedelta

from api_request.wb_requests import (advertisment_campaign_clusters_statistic,
                                     advertisment_campaign_list,
                                     advertisment_campaigns_list_info,
                                     advertisment_statistic_info,
                                     create_auto_advertisment_campaign,
                                     statistic_search_campaign_keywords)
from create_reklama.models import CreatedCampaign
from django.db.models import Q
from motivation.models import Selling
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg
from reklama.models import UrLico

from web_barcode.constants_file import header_wb_dict


def check_data_for_create_adv_campaign(main_data):
    """Обрабатывает и проверяет данные для создания рекламной кампании"""
    raw_articles = main_data['articles']
    ur_lico = UrLico.objects.get(id=main_data['ur_lico'])
    ur_lico_name = ur_lico.ur_lice_name
    campaign_name = main_data['campaign_name']
    campaign_type = int(main_data['select_type'])
    subject_id = int(main_data['select_subject'])
    cpm = int(main_data['cpm'])
    budget = int(main_data['budget'])

    header = header_wb_dict[ur_lico_name]
    result_articles = raw_articles.split(', ')

    errors_list = []
    mns_list = []
    main_articles_list = Articles.objects.filter(
        company=ur_lico).values('wb_nomenclature')
    articles_list = []
    for article in main_articles_list:
        articles_list.append(str(article['wb_nomenclature']))

    # Проверка артикулов на наличие в системе:
    for nmid in result_articles:
        if nmid not in articles_list:
            error = f'Нет артикула <b>{nmid}</b> в на портале у <b>{ur_lico}</b>.'
            errors_list.append(error)
        else:
            mns_list.append(int(nmid))
    # Проверка что название кампании оригинальное:
    campaign_name_list = []
    campaign_queryset = CreatedCampaign.objects.filter(
        ur_lico=ur_lico).values('campaign_name')

    for name in campaign_queryset:
        campaign_name_list.append(name['campaign_name'])

    if campaign_name in campaign_name_list:
        error = (f'''Название кампании <b>{campaign_name}</b> уже существует у кампании юр. лица <b>{ur_lico_name}: {
            CreatedCampaign.objects.get(ur_lico=ur_lico,
                                        campaign_name=campaign_name).campaign_number}</b>''')
        errors_list.append(error)

    if errors_list:
        return errors_list
    else:
        return create_auto_advertisment_campaign(header, campaign_type, campaign_name, subject_id, budget, mns_list, cpm)


def add_created_campaign_data_to_database(main_data):
    """Обрабатывает и проверяет данные для создания рекламной кампании"""

    raw_articles = main_data['articles']
    ur_lico = UrLico.objects.get(id=main_data['ur_lico'])
    ur_lico_name = ur_lico.ur_lice_name
    campaign_number = main_data['campaign_number']
    campaign_name = main_data['campaign_name']
    campaign_type = int(main_data['select_type'])
    subject_id = int(main_data['select_subject'])
    cpm = int(main_data['cpm'])
    budget = int(main_data['budget'])
    today = datetime.now().strftime("%Y-%m-%d %H:%M")

    result_articles = raw_articles.split(', ')
    mns_list = []
    for nmid in result_articles:
        mns_list.append(int(nmid))

    CreatedCampaign(
        ur_lico=ur_lico,
        campaign_name=campaign_name,
        campaign_number=campaign_number,
        camnpaign_type=campaign_name,
        campaign_status=9,
        create_date=today,
        articles_name=mns_list,
        subject_id=subject_id,
        current_cpm=cpm
    ).save()
