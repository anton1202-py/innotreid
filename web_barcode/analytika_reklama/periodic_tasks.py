import math
from datetime import datetime, timedelta

from analytika_reklama.models import (CommonCampaignDescription, KeywordPhrase,
                                      MainArticleExcluded, MainArticleKeyWords,
                                      MainCampaignClusters,
                                      MainCampaignExcluded,
                                      StatisticCampaignKeywordPhrase)
from analytika_reklama.phrase_statistic import add_keyphrase_to_db
from analytika_reklama.wb_supplyment import (
    add_adv_statistic_to_db, save_main_clusters_statistic_for_campaign,
    save_main_keywords_searchcampaign_statistic, type_adv_campaigns)
from api_request.wb_requests import (advertisment_campaign_clusters_statistic,
                                     advertisment_campaigns_list_info,
                                     advertisment_statistic_info,
                                     statistic_keywords_auto_campaign,
                                     statistic_search_campaign_keywords)
from celery_tasks.celery import app
from create_reklama.models import CreatedCampaign
from create_reklama.supplyment import white_list_phrase
from django.db.models import F, Q
from price_system.models import Articles
from reklama.models import UrLico

from web_barcode.constants_file import (CHAT_ID_ADMIN,
                                        WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
                                        WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
                                        bot, header_wb_dict)


@app.task
def add_campaigns_statistic_to_db():
    """
    Собирает статистику о всех кампаниях для всех юр. лиц.

    Переменные:
    main_data - словарь типа {юр_лицо: [список рекламных кампаний в юр. лице]}
    main_adv_data - данные для рекламных кампаний какого-то юр. лица (макс 50 кампаний)
    """
    ur_lico_data = UrLico.objects.all()
    statistic_date_raw = datetime.now() - timedelta(days=9)
    statistic_date_finish = datetime.now().strftime('%Y-%m-%d')
    statistic_date_begin = statistic_date_raw.strftime('%Y-%m-%d')
    for ur_lico_obj in ur_lico_data:
        main_data = CreatedCampaign.objects.filter(
            ur_lico=ur_lico_obj, campaign_status__in=[9, 11])
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
                        "begin": statistic_date_begin,
                        "end": statistic_date_finish
                    }
                }
                data_campaign_list.append(inner_dict)
            header = header_wb_dict[ur_lico_obj.ur_lice_name]
            # print('data_campaign_list', data_campaign_list)
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
        main_data = CreatedCampaign.objects.filter(
            ur_lico=ur_lico_obj, campaign_status__in=[9], campaign_type__in=[8])
        header = header_wb_dict[ur_lico_obj.ur_lice_name]
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
        main_data = CreatedCampaign.objects.filter(
            ur_lico=ur_lico_obj, campaign_type__in=[6, 9])

        header = header_wb_dict[ur_lico_obj.ur_lice_name]
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
    urlico_data = UrLico.objects.all()
    for urlico_obj in urlico_data:
        campaigns = CreatedCampaign.objects.filter(
            ur_lico=urlico_obj)
        header = header_wb_dict[urlico_obj.ur_lice_name]
        for campaign_obj in campaigns:
            campaign_number = campaign_obj.campaign_number
            if type(campaign_obj.articles_name) == int:
                article_obj = Articles.objects.get(company=urlico_obj.ur_lice_name, wb_nomenclature=campaign_obj.articles_name)
                clusters_data = advertisment_campaign_clusters_statistic(header, campaign_number)
                for cluster in clusters_data['clusters']:
                    cluster_name = cluster['cluster']
                    phrase_obj = add_keyphrase_to_db(cluster_name)
                    if not MainArticleKeyWords.objects.filter(
                        article=article_obj,
                        cluster=phrase_obj).exists():
                        MainArticleKeyWords(
                            article=article_obj,
                            cluster=phrase_obj,
                            views=cluster['count']).save()
                    else:
                        MainArticleKeyWords.objects.filter(
                        article=article_obj,
                        cluster=phrase_obj).update(
                            views=cluster['count']
                        )


@app.task
def articles_excluded():
    """Определяем слова исключения для артикула"""

    campaign_with_one_article = MainCampaignExcluded.objects.filter(
        excluded__isnull=False)

    for excluded_obj in campaign_with_one_article:
        articles_name = 0
        if excluded_obj.campaign:
            if type(excluded_obj.campaign.articles_name) == int:
                articles_name = excluded_obj.campaign.articles_name
            elif (type(excluded_obj.campaign.articles_name)) == list:
                articles_name = excluded_obj.campaign.articles_name[0]
            if Articles.objects.filter(
                company=excluded_obj.campaign.ur_lico.ur_lice_name,
                wb_nomenclature=articles_name
            ).exists():
                article_obj = Articles.objects.filter(
                    company=excluded_obj.campaign.ur_lico.ur_lice_name,
                    wb_nomenclature=articles_name
                )[0]
                if not MainArticleExcluded.objects.filter(
                        article=article_obj,
                        excluded=excluded_obj.excluded).exists():
                    MainArticleExcluded(
                        article=article_obj,
                        excluded=excluded_obj.excluded
                    ).save()


@app.task
def get_auto_campaign_statistic_common_data():
    """Получает статистику каждой РК и записывает в базу данных"""
    common_data = CreatedCampaign.objects.all()
    for campaign_obj in common_data:
        header = header_wb_dict[campaign_obj.ur_lico.ur_lice_name]

        campaign_statistic = statistic_keywords_auto_campaign(
            header, int(campaign_obj.campaign_number))['keywords']
        if campaign_statistic:
            for data in campaign_statistic:
                date_str = data['date']
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                date = date_obj - timedelta(days=2)
                today_date = datetime.now(date_obj.tzinfo).replace(
                    hour=0, minute=0, second=0, microsecond=0)
                # if date.date() < today_date.date():
                phrase_stat = data['stats']
                for phrase_data in phrase_stat:
                    phrase = phrase_data['keyword']
                    views = phrase_data['views']
                    clicks = phrase_data['clicks']
                    ctr = phrase_data['ctr']
                    summ = phrase_data['sum']
                    phrase_obj = add_keyphrase_to_db(phrase)
                    if not StatisticCampaignKeywordPhrase.objects.filter(statistic_date=date_str,
                                                                         keyword=phrase_obj,
                                                                         campaign=campaign_obj).exists():
                        StatisticCampaignKeywordPhrase(
                            statistic_date=date_str,
                            keyword=phrase_obj,
                            campaign=campaign_obj,
                            views=views,
                            clicks=clicks,
                            ctr=ctr,
                            summ=summ
                        ).save()
                    else:
                        StatisticCampaignKeywordPhrase.objects.filter(statistic_date=date_str,
                                                                      keyword=phrase_obj,
                                                                      campaign=campaign_obj).update(
                            views=views,
                            clicks=clicks,
                            ctr=ctr,
                            summ=summ
                        )


@app.task
def get_campaigns_amount_in_keyword_phrase():
    """Записывает сколько рекламных кампаний рекламируется в одном ключевом слове"""
    keyword_stats = KeywordPhrase.objects.all()
    for data in keyword_stats:
        counter = 0
        campaigns = StatisticCampaignKeywordPhrase.objects.filter(
            keyword=data).values('campaign').distinct()
        for campaign in campaigns:

            inner_list = []
            white_list = white_list_phrase(campaign['campaign'])
            minus_phrase_campaign_list = MainCampaignExcluded.objects.filter(
                campaign=campaign['campaign']).values('excluded')
            for phrase in minus_phrase_campaign_list:
                if phrase['excluded'] not in white_list:
                    inner_list.append(phrase['excluded'])
            if data.phrase not in inner_list:
                counter += 1
        data.campaigns_amount = counter
        data.save()
