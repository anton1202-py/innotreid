
import json
from datetime import datetime

import pandas as pd
from api_request.wb_requests import (pausa_advertisment_campaigns,
                                     start_advertisment_campaigns)
from create_reklama.models import (AllMinusWords, AutoReplenish, CpmWbCampaign,
                                   CreatedCampaign, ProcentForAd,
                                   ReplenishWbCampaign,
                                   SenderStatisticDaysAmount,
                                   StartPausaCampaign, VirtualBudgetForAd)
from create_reklama.periodic_tasks import (check_replenish_adv_budget, set_up_minus_phrase_to_auto_campaigns,
    update_campaign_status)
from create_reklama.supplyment import (
    check_data_create_adv_campaign_from_excel_file,
    check_data_for_create_adv_campaign,
    create_reklama_excel_with_campaign_data,
    create_reklama_template_excel_file)
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.generic import ListView
from price_system.models import Articles
from reklama.models import DataOooWbArticle, UrLico

from actions.periodic_tasks import add_new_actions_ozon_to_db, add_new_actions_wb_to_db
from actions.supplyment import create_data_with_article_conditions
from web_barcode.constants_file import (SUBJECT_REKLAMA_ID_DICT,
                                        WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
                                        WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
                                        bot, header_wb_dict)


@login_required
def create_campaign(request):
    """Отображает страницу создания кампании"""
    page_name = 'Создание рекламной кампании'
    ur_lico_data = UrLico.objects.all()
    file_add_name = 'OOO'
    check_replenish_adv_budget()
    data = CreatedCampaign.objects.all()
    user_chat_id = request.user.tg_chat_id
    import_data = ''
    errors_list = []
    ok_answer = []
    if request.POST:
        if 'export' in request.POST or 'import_file' in request.FILES:
            if request.POST.get('export') == 'create_file':
                return create_reklama_template_excel_file(ur_lico_data, SUBJECT_REKLAMA_ID_DICT)

            elif 'import_file' in request.FILES:
                errors_list = create_reklama_excel_with_campaign_data(
                    request.FILES['import_file'])
                if type(errors_list) != str:
                    ok_answer = f"Файл {request.FILES['import_file']} принят в работу"
    context = {
        'user_chat_id': user_chat_id,
        'errors_list': errors_list,
        'ok_answer': ok_answer,
        'page_name': page_name,
        'ur_lico_data': ur_lico_data,
        'subject_id': SUBJECT_REKLAMA_ID_DICT,
        'errors_list': errors_list,
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
    campaigns_list = CreatedCampaign.objects.filter(
        ur_lico__ur_lice_name='ООО Иннотрейд')
    statistic_days = SenderStatisticDaysAmount.objects.all()
    ur_lico_data = UrLico.objects.all()
    koef_campaign_data = ProcentForAd.objects.values('campaign_number').annotate(
        latest_add=Max('id')).values('campaign_number', 'latest_add', 'koef_date', 'koefficient', 'virtual_budget', 'campaign_budget_date', 'virtual_budget_date')
    koef_dict = {}
    for koef in koef_campaign_data:
        koef_dict[koef['campaign_number']] = [
            koef['koefficient'], koef['koef_date'], koef['latest_add'], koef['virtual_budget'], koef['campaign_budget_date'], koef['virtual_budget_date']]

    auto_replenish_data = AutoReplenish.objects.values('campaign_number').values(
        'campaign_number', 'auto_replenish', 'auto_replenish_summ')
    auto_replenish = {}
    for auto_rep in auto_replenish_data:
        auto_replenish[auto_rep['campaign_number']] = [
            auto_rep['auto_replenish'], auto_rep['auto_replenish_summ']]
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
        elif 'ur_lico_select' in request.POST:
            filter_ur_lico = request.POST['ur_lico_select']
            campaigns_list = CreatedCampaign.objects.filter(
                ur_lico=filter_ur_lico)
    context = {
        'page_name': page_name,
        'campaigns_list': campaigns_list,
        'ur_lico_data': ur_lico_data,
        'koef_dict': koef_dict,
        'auto_replenish': auto_replenish,
        'statistic_days': statistic_days,
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
    """Запускает или ставит на паузу чекнутые кампании"""
    if request.POST:
        print(request.POST)
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


@login_required
def common_minus_words(request):
    """Общие минус слова для всех кампаний"""
    page_name = 'Общие минус слова для всех кампаний'
    minus_words_list = AllMinusWords.objects.all().order_by('word')
    ur_lico_data = UrLico.objects.all()
    user_chat_id = request.user.tg_chat_id

    if request.POST:
        if 'add_word' in request.POST:
            main_word = request.POST.get('add_minus_word')
            ur_lico_select = request.POST.get('ur_lico_select')
            ur_lico_instance = UrLico.objects.get(id=ur_lico_select)
            if not AllMinusWords.objects.filter(ur_lico=ur_lico_select, word=main_word).exists():
                AllMinusWords(ur_lico=ur_lico_instance, word=main_word).save()
        elif "del-button" in request.POST:
            word_id = request.POST.get('del-button')
            AllMinusWords.objects.filter(id=word_id).delete()

    context = {
        'page_name': page_name,
        'minus_words_list': minus_words_list,
        'ur_lico_data': ur_lico_data,
        'user_chat_id': user_chat_id,
        'WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT': WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
        'WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT': WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
    }
    return render(request, 'create_reklama/minus_words_list.html', context)


def update_common_minus_words(request):
    """Обновляет минус слово, если его исправили"""
    if request.POST:
        if 'main_word' in request.POST:
            main_word = request.POST.get('main_word')
            word_id = request.POST.get('word_id')
            word_object = AllMinusWords.objects.get(id=word_id)
            word_object.word = main_word
            word_object.save()
        return JsonResponse({'message': 'Value saved successfully.'})
    return JsonResponse({'error': 'Invalid request method.'}, status=400)


def apply_all_minus_words(request):
    """
    Применяет все минус слова на юр. лицам на рекламные кампании 
    по юр лицам при нажатии на кнопку ПРИМЕНИТЬ СЛОВА
    """
    if request.POST:
        user_chat_id = int(request.POST.get('user_chat_id'))
        set_up_minus_phrase_to_auto_campaigns()
        message = 'Обновил все минус фразы'
        bot.send_message(chat_id=user_chat_id,
                         text=message)
        return JsonResponse({'message': 'Value saved successfully.'})
    return JsonResponse({'error': 'Invalid request method.'}, status=400)


def wb_article_campaign(request):
    """Отображает ООО артикулы ВБ и к каким кампаниям они относятся"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    data = DataOooWbArticle.objects.all()
    if request.method == 'POST':
        if 'filter' in request.POST:
            filter_data = request.POST
            article_filter = filter_data.get("common_article")
            stock_filter = filter_data.get("stock_amount")
            campaign_filter = filter_data.get("campaign")

            if article_filter:
                article_obj = Articles.objects.get(
                    wb_article=article_filter)
                data = data.filter(
                    Q(wb_article=article_obj)).order_by('wb_article')
            if stock_filter:
                data = data.filter(
                    Q(fbo_amount=int(stock_filter))).order_by('wb_article')
            if campaign_filter:
                data = data.filter(
                    Q(ad_campaign__icontains=campaign_filter)).order_by('wb_article')

    context = {
        'data': data,
    }
    return render(request, 'create_reklama/wb_article_campaign.html', context)


class CampaignCpmStatisticView(ListView):
    model = CreatedCampaign
    template_name = 'create_reklama/create_campaign_cpm_stat.html'
    context_object_name = 'data'

    def __init__(self, *args, **kwargs):
        super(CampaignCpmStatisticView, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(CampaignCpmStatisticView,
                        self).get_context_data(**kwargs)
        campaign_obj = CreatedCampaign.objects.get(id=self.kwargs['id'])
        cpm_data = CpmWbCampaign.objects.filter(campaign_number=campaign_obj)
        context.update({
            'cpm_data': cpm_data,
            'campaign_obj': self.kwargs['id'],
            'campaign_data': campaign_obj,
            'page_name': f"Статистика CPM {campaign_obj.campaign_number}: {campaign_obj.campaign_name}",
        })
        return context


class CampaignReplenishStatisticView(ListView):
    model = CreatedCampaign
    template_name = 'create_reklama/create_campaign_replenish_stat.html'
    context_object_name = 'data'

    def __init__(self, *args, **kwargs):
        super(CampaignReplenishStatisticView, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(CampaignReplenishStatisticView,
                        self).get_context_data(**kwargs)
        campaign_obj = CreatedCampaign.objects.get(id=self.kwargs['id'])
        table_data = {}
        replenish_data = ReplenishWbCampaign.objects.filter(
            campaign_number=campaign_obj)
        for data in replenish_data:
            # Форматирование даты в нужный формат
            formatted_date = data.replenish_date.strftime('%Y-%m-%d')
            print(formatted_date)
            table_data[formatted_date] = {1: data.sum}
        
        virtual_balance_data = VirtualBudgetForAd.objects.filter(
            campaign_number=campaign_obj)
        for data in virtual_balance_data:
            formatted_date = data.virtual_budget_date.strftime('%Y-%m-%d')
            if data.virtual_budget_date in table_data:
                table_data[formatted_date][2] = data.virtual_budget
            else:
                table_data[formatted_date] = {2: data.virtual_budget}

        context.update({
            'table_data': table_data,
            'replenish_data': replenish_data,
            'virtual_balance_data': virtual_balance_data,
            'campaign_obj': self.kwargs['id'],
            'campaign_data': campaign_obj,
            'page_name': f"Статистика пополнения {campaign_obj.campaign_number}: {campaign_obj.campaign_name}",

        })
        return context


class StartPausaStatisticView(ListView):
    model = CreatedCampaign
    template_name = 'create_reklama/create_campaign_pausa_stat.html'
    context_object_name = 'data'

    def __init__(self, *args, **kwargs):
        super(StartPausaStatisticView, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(StartPausaStatisticView,
                        self).get_context_data(**kwargs)
        campaign_obj = CreatedCampaign.objects.get(id=self.kwargs['id'])
        pausa_data = StartPausaCampaign.objects.filter(
            campaign_number=campaign_obj)

        context.update({
            'pausa_data': pausa_data,
            'campaign_obj': self.kwargs['id'],
            'campaign_data': campaign_obj,
            'WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT': WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
            'page_name': f"Статистика остановок {campaign_obj.campaign_number}: {campaign_obj.campaign_name}",
        })
        return context


def update_auto_replenish_sum(request):
    """Обновляет сумму для автопополнения"""
    if request.POST:
        campaign_id = request.POST.get('campaign_id')
        replenish_sum = request.POST.get('replenish_sum')
        campaign_object = CreatedCampaign.objects.get(id=campaign_id)
        if replenish_sum == '':
            replenish_sum = 0
        AutoReplenish.objects.filter(campaign_number=campaign_object).update(
            auto_replenish_summ=replenish_sum)
    return JsonResponse({'message': 'Value saved successfully.'})


def update_checkbox_auto_replenish(request):
    """Обновляет статус о необходимости автопополнения рекламной кампании"""
    if request.POST:
        campaign_id = request.POST.get('campaign_id')
        check_status = request.POST.get('is_checked')
        status = False
        if check_status == 'true':
            status = True
        campaign_object = CreatedCampaign.objects.get(id=campaign_id)
        AutoReplenish.objects.filter(campaign_number=campaign_object).update(
            auto_replenish=status)
    return JsonResponse({'message': 'Value saved successfully.'})


def create_reklama_from_excel(request):
    """Обрабатывает Excel файл для создания рекламных кампаний"""
    if 'export' in request.POST or 'import_file' in request.FILES:
        if 'import_file' in request.FILES:
            user_chat_id = int(request.POST.get('user_chat_id'))

            import_data = create_reklama_excel_with_campaign_data(
                request.FILES['import_file'])
            if type(import_data) == str:
                return HttpResponse(f"Вы пытались загрузить ошибочный файл {request.FILES['import_file']}.")
            excel_data_common = pd.read_excel(request.FILES['import_file'])
            column_list = excel_data_common.columns.tolist()

            excel_data = pd.DataFrame(excel_data_common, columns=[
                                      'Юр. лицо', 'Тип кампании', 'Предмет', 'Артикул WB (nmID)', 'Бюджет', 'Ставка'])
            article_list = excel_data['Артикул WB (nmID)'].to_list()
            ur_lico_list = excel_data['Юр. лицо'].to_list()
            type_list = excel_data['Тип кампании'].to_list()
            subject_list = excel_data['Предмет'].to_list()
            budget_list = excel_data['Бюджет'].to_list()
            cpm_list = excel_data['Ставка'].to_list()
            main_articles_list = Articles.objects.all().values('wb_nomenclature')
            articles_list = []
            mns_list = []
            for article in main_articles_list:
                articles_list.append(str(article['wb_nomenclature']))

            # Проверка артикулов на наличие в системе:

            for i in range(len(article_list)):
                if str(article_list[i]) != 'nan':
                    nmid = str(int(article_list[i]))
                    ur_lico = ur_lico_list[i]
                    campaign_type = 8
                    subject_id = SUBJECT_REKLAMA_ID_DICT[subject_list[i]]
                    budget = int(budget_list[i])
                    cpm = int(cpm_list[i])
                    check_data_create_adv_campaign_from_excel_file(
                        articles_list, nmid, ur_lico, user_chat_id, campaign_type, subject_id, budget, cpm)
            return HttpResponse(f'Файл {request.FILES["import_file"]} успешно обработан')
        else:
            return HttpResponse('Неправильный формат файла')

    return HttpResponse('Ошибка при загрузке файла')


def days_sender_statistic(request):
    """Обновляет количество дней для отрпавки статистики в телеграм"""

    if request.POST:
        print(request.POST)
        days = int(request.POST.get('days'))

        SenderStatisticDaysAmount.objects.filter(id=1).update(days_amount=days)

    return HttpResponse('Запрос обработался')
