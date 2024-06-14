import math
from datetime import datetime, timedelta

from analytika_reklama.models import (CommonCampaignDescription,
                                      MainArticleExcluded, MainArticleKeyWords,
                                      MainCampaignClusters,
                                      MainCampaignExcluded)
from analytika_reklama.wb_supplyment import (
    add_adv_data_to_db_about_all_campaigns, add_adv_statistic_to_db,
    save_main_clusters_statistic_for_campaign,
    save_main_keywords_searchcampaign_statistic, type_adv_campaigns)
from api_request.wb_requests import (advertisment_campaign_clusters_statistic,
                                     advertisment_campaigns_list_info,
                                     advertisment_statistic_info,
                                     statistic_search_campaign_keywords)
from celery_tasks.celery import app
from django.db.models import Q
from price_system.models import Articles
from reklama.models import UrLico

from web_barcode.constants_file import (CHAT_ID_ADMIN,
                                        WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
                                        WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
                                        bot, header_wb_data_dict)


@app.task
def add_info_to_db_about_all_campaigns():
    """
    Собирает информацию о всех кампаниях для всех юр. лиц.

    Переменные:
    main_data - словарь типа {юр_лицо: [список рекламных кампаний в юр. лице]}
    main_adv_data - данные для рекламных кампаний какого-то юр. лица (макс 50 кампаний)
    """
    main_data = type_adv_campaigns()

    for ur_lico, adv_list in main_data.items():
        koef_product = math.ceil(len(adv_list)/50)
        for i in range(koef_product):
            start_point = i*50
            finish_point = (i+1)*50
            adv_current_list = adv_list[
                start_point:finish_point]
            header = header_wb_data_dict[ur_lico]
            main_adv_data = advertisment_campaigns_list_info(
                adv_current_list, header)
            # Записываем/обновляем информацию о РК в базу данных
            add_adv_data_to_db_about_all_campaigns(ur_lico, main_adv_data)


@app.task
def add_campaigns_statistic_to_db():
    """
    Собирает статистику о всех кампаниях для всех юр. лиц.

    Переменные:
    main_data - словарь типа {юр_лицо: [список рекламных кампаний в юр. лице]}
    main_adv_data - данные для рекламных кампаний какого-то юр. лица (макс 50 кампаний)
    """
    ur_lico_data = UrLico.objects.all()
    statistic_date_raw = datetime.now() - timedelta(days=1)
    statistic_date = statistic_date_raw.strftime('%Y-%m-%d')
    for ur_lico_obj in ur_lico_data:
        main_data = CommonCampaignDescription.objects.filter(
            ur_lico=ur_lico_obj, camnpaign_status__in=[9, 11])
        koef_product = math.ceil(len(main_data)/100)
        for i in range(koef_product):
            start_point = i*100
            finish_point = (i+1)*100
            adv_current_list = main_data[
                start_point:finish_point]
            data_campaign_list = []
            for campaign in adv_current_list:
                inner_dict = {
                    "id": int(campaign.campaign_number),
                    "interval": {
                        "begin": statistic_date,
                        "end": statistic_date
                    }
                }
                data_campaign_list.append(inner_dict)
            header = header_wb_data_dict[ur_lico_obj.ur_lice_name]
            main_adv_data = advertisment_statistic_info(
                data_campaign_list, header)
            if main_adv_data:
                # Записываем/обновляем информацию о РК в базу данных
                add_adv_statistic_to_db(ur_lico_obj, main_adv_data)


@app.task
def get_clusters_statistic_for_autocampaign():
    """
    Получает общую статистику автоматической рекламной кампании по кластерам
    ur_lico - юр. лицо
    campaign_data_list - данные для рекламных кампаний ur_lico юр. лица (макс 50 кампаний)
    """
    ur_lico_data = UrLico.objects.all()
    main_data_dict = {}
    for ur_lico_obj in ur_lico_data:
        main_data = CommonCampaignDescription.objects.filter(
            ur_lico=ur_lico_obj, camnpaign_status__in=[9], camnpaign_type__in=[8])
        header = header_wb_data_dict[ur_lico_obj.ur_lice_name]
        for campaign_data in main_data:
            campaign_number = campaign_data.campaign_number
            clusters = advertisment_campaign_clusters_statistic(
                header, campaign_number)
            # Добавляем статистику по кластерам к кампании
            save_main_clusters_statistic_for_campaign(campaign_data, clusters)


@app.task
def get_searchcampaign_keywords_statistic():
    """
    Получает общую статистику рекламной кампании поиск и поиск + каталог по ключевым фразам
    """
    ur_lico_data = UrLico.objects.all()
    main_data_dict = {}
    for ur_lico_obj in ur_lico_data:
        main_data = CommonCampaignDescription.objects.filter(
            ur_lico=ur_lico_obj, camnpaign_type__in=[6, 9])

        header = header_wb_data_dict[ur_lico_obj.ur_lice_name]
        for campaign_data in main_data:
            campaign_number = campaign_data.campaign_number
            keywords_data = statistic_search_campaign_keywords(
                header, campaign_number)
            if keywords_data:
                # Добавляем статистику по кластерам к кампании
                save_main_keywords_searchcampaign_statistic(
                    campaign_data, keywords_data)


@app.task
def keyword_for_articles():
    """Определяем артикулы, которым можем приписать кластеры и ключевые слова"""

    campaign_with_one_article = MainCampaignClusters.objects.filter(
        Q(cluster__isnull=False) & Q(campaign__articles_amount=1))

    for cluster_obj in campaign_with_one_article:
        articles_name = 0
        if type(cluster_obj.campaign.articles_name) == int:
            articles_name = cluster_obj.campaign.articles_name
        elif (type(cluster_obj.campaign.articles_name)) == list:
            articles_name = cluster_obj.campaign.articles_name[0]
        if Articles.objects.filter(
            company=cluster_obj.campaign.ur_lico.ur_lice_name,
            wb_nomenclature=articles_name
        ).exists():
            article_obj = Articles.objects.get(
                company=cluster_obj.campaign.ur_lico.ur_lice_name,
                wb_nomenclature=articles_name
            )
            if not MainArticleKeyWords.objects.filter(
                    article=article_obj,
                    cluster=cluster_obj.cluster).exists():
                MainArticleKeyWords(
                    article=article_obj,
                    cluster=cluster_obj.cluster,
                    views=cluster_obj.count).save()


@app.task
def articles_excluded():
    """Определяем слова исключения для артикула"""

    campaign_with_one_article = MainCampaignExcluded.objects.filter(
        Q(excluded__isnull=False) & Q(campaign__articles_amount=1))

    for excluded_obj in campaign_with_one_article:
        articles_name = 0
        if type(excluded_obj.campaign.articles_name) == int:
            articles_name = excluded_obj.campaign.articles_name
        elif (type(excluded_obj.campaign.articles_name)) == list:
            articles_name = excluded_obj.campaign.articles_name[0]
        if Articles.objects.filter(
            company=excluded_obj.campaign.ur_lico.ur_lice_name,
            wb_nomenclature=articles_name
        ).exists():
            article_obj = Articles.objects.get(
                company=excluded_obj.campaign.ur_lico.ur_lice_name,
                wb_nomenclature=articles_name
            )
            if not MainArticleExcluded.objects.filter(
                    article=article_obj,
                    excluded=excluded_obj.excluded).exists():
                MainArticleExcluded(
                    article=article_obj,
                    excluded=excluded_obj.excluded
                ).save()
