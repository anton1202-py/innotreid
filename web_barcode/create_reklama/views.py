import time

from analytika_reklama.models import (CommonCampaignDescription,
                                      DailyCampaignParameters,
                                      MainArticleExcluded, MainArticleKeyWords,
                                      MainCampaignClusters,
                                      MainCampaignParameters)
from analytika_reklama.periodic_tasks import (
    add_campaigns_statistic_to_db, add_info_to_db_about_all_campaigns,
    get_clusters_statistic_for_autocampaign,
    get_searchcampaign_keywords_statistic)
from create_reklama.models import CreatedCampaign
from create_reklama.supplyment import (add_created_campaign_data_to_database,
                                       check_data_for_create_adv_campaign)
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import ListView
from price_system.models import Articles
from reklama.models import UrLico
from users.models import InnotreidUser

from web_barcode.constants_file import (CHAT_ID_ADMIN,
                                        WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
                                        WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
                                        bot, header_wb_data_dict,
                                        header_wb_dict)


@login_required
def create_campaign(request):
    """Отображает страницу создания кампании"""
    page_name = 'Создание рекламной кампании'

    ur_lico_data = UrLico.objects.all()
    subject_id = {
        'Ночник': 1673,
        'Грамота/диплом': 3618,
        'Файл вкладыш': 3169
    }
    user_chat_id = request.user.tg_chat_id

    errors_list = []
    ok_answer = []
    if request.POST:
        ur_lico = request.POST.get('ur_lico_select')
        select_type = request.POST.get('select_type')
        campaign_name = request.POST.get('name')
        select_subject = request.POST.get('select_subject')
        articles = request.POST.get('articles')
        budget = request.POST.get('budget')
        cpm = request.POST.get('cpm')

        main_data = {
            'ur_lico': ur_lico,
            'select_type': select_type,
            'campaign_name': campaign_name,
            'select_subject': select_subject,
            'articles': articles,
            'cpm': cpm,
            'budget': budget
        }

    context = {
        'user_chat_id': user_chat_id,
        'errors_list': errors_list,
        'ok_answer': ok_answer,
        'page_name': page_name,
        'ur_lico_data': ur_lico_data,
        'subject_id': subject_id,
        'WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT': WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
        'WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT': WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
    }
    return render(request, 'create_reklama/create_campaign.html', context)


def create_many_campaigns(request):
    """Создает много кампаний"""

    if request.method == 'POST':
        # Получение данных из формы
        ur_lico = request.POST.get('ur_lico_select')
        select_type = request.POST.get('select_type')
        campaign_name = request.POST.get('name')
        select_subject = request.POST.get('select_subject')
        articles = request.POST.get('articles')
        budget = request.POST.get('budget')
        cpm = request.POST.get('cpm')
        user_chat_id = request.POST.get('user_chat_id')

        main_data = {
            'ur_lico': ur_lico,
            'select_type': select_type,
            'campaign_name': campaign_name,
            'select_subject': select_subject,
            'articles': articles,
            'cpm': cpm,
            'budget': budget,
            'user_chat_id': user_chat_id
        }
        check_data_for_create_adv_campaign(main_data)
    return JsonResponse({"status": "Function is still running in the background."})


@login_required
def campaigns_were_created_with_system(request):
    """Отображает созданные кампании через эту систему"""
    page_name = 'Созданные рекламные кампании'
    campaigns_list = CreatedCampaign.objects.all()
    ur_lico_data = UrLico.objects.all()

    if request.POST:
        ur_lico = request.POST.get('ur_lico_select')
        select_type = request.POST.get('select_type')
        campaign_name = request.POST.get('name')
        select_subject = request.POST.get('select_subject')
        articles = request.POST.get('articles')
        budget = request.POST.get('budget')
        cpm = request.POST.get('cpm')

    context = {
        'page_name': page_name,
        'campaigns_list': campaigns_list,
        'ur_lico_data': ur_lico_data,
        'WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT': WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
        'WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT': WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
    }
    return render(request, 'create_reklama/campaigns_list.html', context)
