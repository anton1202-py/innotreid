from datetime import datetime, timedelta

from analytika_reklama.models import (DailyCampaignParameters,
                                      MainCampaignClusters,
                                      MainCampaignClustersKeywords,
                                      MainCampaignExcluded,
                                      MainCampaignParameters)
from analytika_reklama.phrase_statistic import add_keyphrase_to_db
from api_request.wb_requests import advertisment_campaign_list
from create_reklama.models import CreatedCampaign
from price_system.supplyment import sender_error_to_tg

from web_barcode.constants_file import (CHAT_ID_ADMIN,
                                        WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
                                        WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
                                        bot, header_wb_dict)


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
    header_wb_dict - словарь с хедерами для каждого юр. лица
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
    for ur_lico, header in header_wb_dict.items():
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
def add_adv_statistic_to_db(ur_lico: str, campaign_data_list: list):
    """
    Записывает информацию в базу данных о всех входящих кампаний.
    входящие данные:
    ur_lico - юр. лицо
    campaign_data_list - данные для рекламных кампаний ur_lico юр. лица (макс 50 кампаний)
    """
    for main_data in campaign_data_list:
        campaign_data = main_data['advertId']
        for data in main_data['days']:

            campaign = CreatedCampaign.objects.get(
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
            statistic_date = data['date']

            formatted_date = datetime.strptime(
                statistic_date, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%d')
            delta = datetime.today() - timedelta(days=1)
            delta = delta.strftime('%Y-%m-%d')
            if formatted_date == delta:
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

            if not DailyCampaignParameters.objects.filter(campaign=campaign, statistic_date=statistic_date).exists():
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
            else:
                DailyCampaignParameters.objects.filter(campaign=campaign, statistic_date=statistic_date).update(
                    views=views,
                    clicks=clicks,
                    summ=summ,
                    atbs=atbs,
                    orders=orders,
                    shks=shks,
                    ctr=ctr,
                    cpc=cpc,
                    cr=cr
                )


@sender_error_to_tg
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
            if not MainCampaignExcluded.objects.filter(campaign=campaign_obj, excluded=str(incoming_frase)).exists():
                MainCampaignExcluded(
                    campaign=campaign_obj,
                    excluded=str(incoming_frase)).save()
    if incoming_clusters:
        for clusters_data in incoming_clusters:
            cluster_obj = add_keyphrase_to_db(clusters_data['cluster'])
            if not MainCampaignClusters.objects.filter(campaign=campaign_obj, cluster=cluster_obj).exists():
                MainCampaignClusters(
                    campaign=campaign_obj,
                    cluster=cluster_obj,
                    count=clusters_data['count']
                ).save()
            else:
                current_cluster_obj = MainCampaignClusters.objects.get(
                    campaign=campaign_obj, cluster=cluster_obj)
                current_cluster_obj.count = clusters_data['count']
                current_cluster_obj.save()

            if 'keywords' in clusters_data.keys():
                cluster__keyword_obj = MainCampaignClusters.objects.get(
                    campaign=campaign_obj, cluster=cluster_obj)

                for incoming_keywords in clusters_data['keywords']:
                    if not MainCampaignClustersKeywords.objects.filter(
                            cluster=cluster__keyword_obj, keywords=incoming_keywords).exists():
                        MainCampaignClustersKeywords(
                            cluster=cluster__keyword_obj,
                            keywords=incoming_keywords).save()


@sender_error_to_tg
def save_main_keywords_searchcampaign_statistic(campaign_obj, keywords_data):
    """
    Сохраняет статистику ключевых слов для кампаний поиска

    Входящие данные:
    campaign_obj - объект кампании, для которой будет сохраняться статистика
    keyword_data - информация о кластерах
    """

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
            cluster_obj = add_keyphrase_to_db(str(keyword['keyword']))
            if not MainCampaignClusters.objects.filter(campaign=campaign_obj, cluster=cluster_obj).exists():
                MainCampaignClusters(
                    campaign=campaign_obj,
                    cluster=cluster_obj,
                    count=(keyword['count'])
                ).save()
            else:
                current_cluster_obj = MainCampaignClusters.objects.get(
                    campaign=campaign_obj, cluster=cluster_obj)
                current_cluster_obj.count = keyword['count']
                current_cluster_obj.save()
