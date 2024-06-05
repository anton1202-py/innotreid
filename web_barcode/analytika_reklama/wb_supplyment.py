import math
import time
from datetime import datetime, timedelta

from analytika_reklama.models import (CommonCampaignDescription,
                                      DailyCampaignParameters,
                                      MainCampaignClusters,
                                      MainCampaignClustersKeywords,
                                      MainCampaignExcluded,
                                      MainCampaignParameters)
from api_request.wb_requests import (advertisment_campaign_clusters_statistic,
                                     advertisment_campaign_list,
                                     advertisment_campaigns_list_info,
                                     advertisment_statistic_info,
                                     statistic_search_campaign_keywords)
from motivation.models import Selling
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg
from reklama.models import UrLico

from web_barcode.constants_file import (CHAT_ID_ADMIN,
                                        WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
                                        WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
                                        bot, header_wb_data_dict)


@sender_error_to_tg
def type_adv_campaigns():
    """
    Получает и распределяет кампании по типу и статусу для каждого юр лица
    Описание типов кампании:
    4 - в каталоге
    5 - в карточке товара
    6 - в поиске
    7 - в рекомендациях на главной странице
    8 - автоматическая
    9 - поиск + каталог

    Описание статусов кампаний
    -1 - в процессе удаления
    4 - готова к запуску
    7 - завершена
    8 - отказался
    9 - идут показы
    11 - на паузе

    return dict{ur_lico: [список рекламных кампаний]}

    Переменные:
    adv_campaigns_ur_lico_dict - возвращаемый словарь
    header_wb_data_dict - словарь с хедерами для каждого юр. лица
    main_data - данные, полученные от метода https://advert-api.wb.ru/adv/v1/promotion/count
    campaign_inner_list - список со всеми кампаниями юр. лица

    main_data['adverts'] - список словарей для каждого типа и статуса кампаний. 
        {
            "type": 8,
            "status": 11,
            "count": 3,
            "advert_list": []
        }
    data['advert_list'] - список словарей с каждой РК типа {id_кампании: id, дата_изменения: дата}
    campaign_id['advertId'] - id каждой рекламной кампании

    """
    adv_campaigns_ur_lico_dict = {}
    for ur_lico, header in header_wb_data_dict.items():
        # Достаю список кампаний из каждого юр лица
        main_data = advertisment_campaign_list(header)
        # Прохожу по каждой и собираю их в список для каждого юр. лица
        campaign_inner_list = []
        if main_data['adverts']:
            for data in main_data['adverts']:
                for campaign_id in data['advert_list']:
                    campaign_inner_list.append(campaign_id['advertId'])
        adv_campaigns_ur_lico_dict[ur_lico] = campaign_inner_list
    return adv_campaigns_ur_lico_dict


@sender_error_to_tg
def add_adv_data_to_db_about_all_campaigns(ur_lico: str, campaign_data_list: list):
    """
    Записывает информацию в базу данных о всех входящих кампаний.
    входящие данные:
    ur_lico - юр. лицо
    campaign_data_list - данные для рекламных кампаний ur_lico юр. лица (макс 50 кампаний)
    """
    for data in campaign_data_list:
        campaign_number = data['advertId']
        campaign_name = str(data['name'])
        camnpaign_type = data['type']
        camnpaign_status = data['status']
        if 'autoParams' in data.keys() and data['autoParams']['nms']:
            articles_amount = len(data['autoParams']['nms'])
            articles_name = data['autoParams']['nms']
        elif 'params' in data.keys() and data['params'][0]['nms']:
            articles_amount = len(data['params'][0]['nms'])
            articles_name = data['params'][0]['nms'][0]['nm']
        elif 'unitedParams' in data.keys() and data['unitedParams'][0]['nms']:
            articles_amount = len(data['unitedParams'][0]['nms'])
            articles_name = data['unitedParams'][0]['nms']
        else:
            articles_amount = 0
            articles_name = None
        create_date = data['createTime']
        change_date = data['changeTime']
        start_date = data['startTime']
        finish_date = data['endTime']
        ur_lico = UrLico.objects.get(ur_lice_name=ur_lico)
        if CommonCampaignDescription.objects.filter(ur_lico=ur_lico, campaign_number=campaign_number).exists():
            campaign_obj = CommonCampaignDescription.objects.get(
                ur_lico=ur_lico, campaign_number=campaign_number)
            campaign_obj.campaign_name = campaign_name
            campaign_obj.camnpaign_type = camnpaign_type
            campaign_obj.camnpaign_status = camnpaign_status
            campaign_obj.articles_amount = articles_amount
            campaign_obj.articles_name = articles_name
            campaign_obj.create_date = create_date
            campaign_obj.change_date = change_date
            campaign_obj.start_date = start_date
            campaign_obj.finish_date = finish_date
            campaign_obj.save()
        else:
            CommonCampaignDescription(
                ur_lico=ur_lico,
                campaign_number=campaign_number,
                campaign_name=campaign_name,
                camnpaign_type=camnpaign_type,
                camnpaign_status=camnpaign_status,
                articles_amount=articles_amount,
                articles_name=articles_name,
                create_date=create_date,
                change_date=change_date,
                start_date=start_date,
                finish_date=finish_date).save()


def add_adv_statistic_to_db(ur_lico: str, campaign_data_list: list):
    """
    Записывает информацию в базу данных о всех входящих кампаний.
    входящие данные:
    ur_lico - юр. лицо
    campaign_data_list - данные для рекламных кампаний ur_lico юр. лица (макс 50 кампаний)
    """
    print(ur_lico, campaign_data_list)
    for data in campaign_data_list:
        campaign_data = data['advertId']
        campaign = CommonCampaignDescription.objects.get(
            ur_lico=ur_lico, campaign_number=campaign_data)
        views = data['views']
        clicks = data['clicks']
        ctr = data['ctr']
        cpc = data['cpc']
        summ = data['sum']
        atbs = data['atbs']
        orders = data['orders']
        cr = data['cr']
        shks = data['shks']
        sum_price = data['sum_price']
        statistic_date = data['interval']['end']
        if MainCampaignParameters.objects.filter(campaign=campaign).exists():

            campaign_params_obj = MainCampaignParameters.objects.get(
                campaign=campaign)
            campaign_params_obj.views += views
            campaign_params_obj.clicks += clicks
            campaign_params_obj.summ += summ
            campaign_params_obj.atbs += atbs
            campaign_params_obj.orders += orders
            campaign_params_obj.shks += shks
            campaign_params_obj.sum_price += sum_price

            campaign_params_obj.ctr = round(
                (campaign_params_obj.clicks/campaign_params_obj.views)*100, 2)
            if campaign_params_obj.clicks != 0:
                campaign_params_obj.cpc = round(
                    campaign_params_obj.summ/campaign_params_obj.clicks, 2)
                campaign_params_obj.cr = round(
                    campaign_params_obj.orders/campaign_params_obj.clicks, 2)
            else:
                campaign_params_obj.cpc = 0
                campaign_params_obj.cr = 0

            campaign_params_obj.save()

        else:
            MainCampaignParameters(
                campaign=campaign,
                views=views,
                clicks=clicks,
                summ=summ,
                atbs=atbs,
                orders=orders,
                shks=shks,
                ctr=ctr,
                cpc=cpc,
                cr=cr
            ).save()

        if not DailyCampaignParameters.objects.filter(campaign=campaign, statistic_date=statistic_date,).exists():
            DailyCampaignParameters(
                campaign=campaign,
                statistic_date=statistic_date,
                views=views,
                clicks=clicks,
                summ=summ,
                atbs=atbs,
                orders=orders,
                shks=shks,
                ctr=ctr,
                cpc=cpc,
                cr=cr
            ).save()


def get_catalog_searchcampaign_keywords_statistic():
    """
    Получает общую статистику рекламной кампании каталог + поиск по ключевым фразам

    """
    ur_lico_data = UrLico.objects.all()
    main_data_dict = {}
    for ur_lico_obj in ur_lico_data:
        main_data = CommonCampaignDescription.objects.filter(
            ur_lico=ur_lico_obj, camnpaign_type__in=[9])

        header = header_wb_data_dict[ur_lico_obj.ur_lice_name]
        for campaign_data in main_data:
            campaign_number = campaign_data.campaign_number
            print(ur_lico_obj, campaign_data.camnpaign_status, campaign_number)
            # keywords_data = statistic_search_campaign_keywords(
            #     header, campaign_number)
            # time.sleep(0.25)
            # # Добавляем статистику по кластерам к кампании
            # save_main_keywords_searchcampaign_statistic(
            #     campaign_data, keywords_data)


def save_main_clusters_statistic_for_campaign(campaign_obj, clusters_info):
    """
    Сохраняет статистику кластера для кампании.

    Входящие данные:
    campaign_obj - объект кампании, для которой будет сохраняться статистика
    clusters_info - информация о кластерах
    """
    incoming_excluded_frases = clusters_info['excluded']
    incoming_clusters = clusters_info['clusters']
    if incoming_excluded_frases:
        for incoming_frase in incoming_excluded_frases:
            if not MainCampaignExcluded.objects.filter(campaign=campaign_obj, excluded=incoming_frase).exists():
                MainCampaignExcluded(
                    campaign=campaign_obj,
                    excluded=str(incoming_frase)).save()
    if incoming_clusters:
        for clusters_data in incoming_clusters:
            if not MainCampaignClusters.objects.filter(campaign=campaign_obj, cluster=clusters_data['cluster']).exists():
                MainCampaignClusters(
                    campaign=campaign_obj,
                    cluster=clusters_data['cluster'],
                    count=clusters_data['count']
                ).save()
            else:
                current_cluster_obj = MainCampaignClusters.objects.get(
                    campaign=campaign_obj, cluster=clusters_data['cluster'])
                current_cluster_obj.count = clusters_data['count']
                current_cluster_obj.save()

            if 'keywords' in clusters_data.keys():
                cluster_obj = MainCampaignClusters.objects.get(
                    campaign=campaign_obj, cluster=clusters_data['cluster'])

                for incoming_keywords in clusters_data['keywords']:
                    if not MainCampaignClustersKeywords.objects.filter(
                            cluster=cluster_obj, keywords=incoming_keywords).exists():
                        MainCampaignClustersKeywords(
                            cluster=cluster_obj,
                            keywords=incoming_keywords).save()
        print('Сохранил кластер')


def save_main_keywords_searchcampaign_statistic(campaign_obj, keywords_data):
    """
    Сохраняет статистику ключевых слов для кампаний поиска

    Входящие данные:
    campaign_obj - объект кампании, для которой будет сохраняться статистика
    keyword_data - информация о кластерах
    """
    print(keywords_data)

    incoming_excluded_frases = keywords_data['words']
    incoming_keywords = []
    if 'keywords' in keywords_data['words']:
        incoming_keywords = keywords_data['words']['keywords']
    excluded_data_list = []
    if incoming_excluded_frases['phrase']:
        excluded_data_list.append(incoming_excluded_frases['phrase'])
    if incoming_excluded_frases['strong']:
        excluded_data_list.append(incoming_excluded_frases['strong'])
    if incoming_excluded_frases['excluded']:
        excluded_data_list.append(incoming_excluded_frases['excluded'])
    if excluded_data_list:
        for frase_data in excluded_data_list:
            for frase in frase_data:
                if frase is str:
                    if not MainCampaignExcluded.objects.filter(campaign=campaign_obj, excluded=str(frase)).exists():
                        MainCampaignExcluded(
                            campaign=campaign_obj,
                            excluded=str(frase)).save()
    if incoming_keywords:
        for keyword in incoming_keywords:
            if not MainCampaignClusters.objects.filter(campaign=campaign_obj, cluster=str(keyword['keyword'])).exists():
                MainCampaignClusters(
                    campaign=campaign_obj,
                    cluster=str(keyword['keyword']),
                    count=(keyword['count'])
                ).save()
            else:
                current_cluster_obj = MainCampaignClusters.objects.get(
                    campaign=campaign_obj, cluster=str(keyword['keyword']))
                current_cluster_obj.count = keyword['count']
                current_cluster_obj.save()
        print('Сохранил кластер')
