
import json
from datetime import datetime

from api_request.wb_requests import (pausa_advertisment_campaigns,
                                     start_advertisment_campaigns)
from create_reklama.add_balance import ad_list, count_sum_orders
from create_reklama.models import AllMinusWords, CreatedCampaign, ProcentForAd
from create_reklama.periodic_tasks import (budget_working,
                                           update_campaign_status)
from create_reklama.supplyment import check_data_for_create_adv_campaign
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from reklama.models import UrLico

from web_barcode.constants_file import (CHAT_ID_ADMIN,
                                        WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
                                        WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
                                        bot, header_wb_data_dict,
                                        header_wb_dict)


@login_required
def create_campaign(request):
    """Отображает страницу создания кампании"""
    page_name = 'Создание рекламной кампании'
    camps = CreatedCampaign.objects.all()
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    for camp_obj in camps:
        if not ProcentForAd.objects.filter(campaign_number=camp_obj):
            ProcentForAd(
                campaign_number=camp_obj,
                koefficient=4,
                koef_date=today,
                virtual_budget=0,
                virtual_budget_date=today,
                campaign_budget_date=today
            ).save()
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
        pass

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
    campaigns_list = CreatedCampaign.objects.all().order_by('ur_lico')
    ur_lico_data = UrLico.objects.all()
    budget_working()
    koef_campaign_data = ProcentForAd.objects.values('campaign_number').annotate(
        latest_add=Max('id')).values('campaign_number', 'latest_add', 'koef_date', 'koefficient', 'virtual_budget', 'campaign_budget_date', 'virtual_budget_date')
    koef_dict = {}
    for koef in koef_campaign_data:
        koef_dict[koef['campaign_number']] = [
            koef['koefficient'], koef['koef_date'], koef['latest_add'], koef['virtual_budget'], koef['campaign_budget_date'], koef['virtual_budget_date']]

    for_pausa_data = []
    for campaign_obj in campaigns_list:
        for_pausa_data.append({'campaign_number': campaign_obj.campaign_number,
                              'ur_lico': campaign_obj.ur_lico.ur_lice_name})

    if request.POST:
        request_data = request.POST
        if 'article_price' in request.POST or 'less_article_price' in request.POST:
            if request.POST['article_price']:
                price = int(request.POST.get('article_price'))
                campaigns_list = CreatedCampaign.objects.filter(
                    article_price_on_page__gte=price)
            elif request.POST['less_article_price']:
                price = int(request.POST.get('less_article_price'))
                campaigns_list = CreatedCampaign.objects.filter(
                    article_price_on_page__lt=price)
        elif 'update_data' in request.POST:
            update_campaign_status()
            return redirect('campaigns_list')

    context = {
        'page_name': page_name,
        'campaigns_list': campaigns_list,
        'ur_lico_data': ur_lico_data,
        'koef_dict': koef_dict,
        'WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT': WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
        'WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT': WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
    }
    return render(request, 'create_reklama/campaigns_list.html', context)


def change_percent_for_advert(request):
    """Изменяет процент пополнения для рекламной кампании"""
    if request.POST:
        percent = int(request.POST.get('main_percent'))
        campaign_id = request.POST.get('campaign_number')
        ur_lico = request.POST.get('ur_lico')
        change_data = ProcentForAd.objects.get(
            campaign_number=campaign_id
        )
        change_data.koefficient = percent
        change_data.koef_date = datetime.now()
        change_data.save()
    return JsonResponse({'ok': 'Удача.'})


def start_checked_campaigns(request):
    """Запускает чекнутые кампании"""
    if request.POST:
        if request.POST['button_name'] == 'startCampaignsBtn':
            for campaign_number, ur_lico in json.loads(request.POST['campaignData']).items():
                if campaign_number != 'null':
                    header = header_wb_dict[ur_lico]
                    start_advertisment_campaigns(header, campaign_number)
        elif request.POST['button_name'] == 'pausaCampaignsBtn':
            for campaign_number, ur_lico in json.loads(request.POST['campaignData']).items():
                if campaign_number != 'null':
                    header = header_wb_dict[ur_lico]
                    pausa_advertisment_campaigns(header, campaign_number)
    return JsonResponse({'error': 'Invalid request method.'})


def pausa_checked_campaigns(request):
    """Ставит на паузу чекнутые кампании"""
    if request.POST:
        for campaign_number, ur_lico in request.POST.items():
            if campaign_number != 'csrfmiddlewaretoken' and campaign_number != 'null':
                header = header_wb_dict[ur_lico]
                # start_advertisment_campaigns(header, campaign_number)
    return JsonResponse({'error': 'Invalid request method.'})


@login_required
def common_minus_words(request):
    """Общие минус слова для всех кампаний"""
    page_name = 'Общие минус слова для всех кампаний'
    minus_words_list = AllMinusWords.objects.all().order_by('word')
    ur_lico_data = UrLico.objects.all()

    if request.POST:
        if 'add_word' in request.POST:
            main_word = request.POST.get('add_minus_word')
            if not AllMinusWords.objects.filter(word=main_word).exists():
                AllMinusWords(word=main_word).save()
        elif "del-button" in request.POST:
            word_id = request.POST.get('del-button')
            AllMinusWords.objects.filter(id=word_id).delete()

    context = {
        'page_name': page_name,
        'minus_words_list': minus_words_list,
        'ur_lico_data': ur_lico_data,
        'WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT': WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
        'WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT': WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
    }
    return render(request, 'create_reklama/minus_words_list.html', context)


def update_common_minus_words(request):
    if request.POST:
        if 'main_word' in request.POST:
            main_word = request.POST.get('main_word')
            word_id = request.POST.get('word_id')
            word_object = AllMinusWords.objects.get(id=word_id)
            word_object.word = main_word
            word_object.save()
        return JsonResponse({'message': 'Value saved successfully.'})
    return JsonResponse({'error': 'Invalid request method.'}, status=400)
