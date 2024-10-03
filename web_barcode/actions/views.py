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
from create_reklama.periodic_tasks import (set_up_minus_phrase_to_auto_campaigns,
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
from actions.models import Action, ArticleInActionWithCondition
from web_barcode.constants_file import (SUBJECT_REKLAMA_ID_DICT,
                                        WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
                                        WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
                                        bot, header_wb_dict)


@login_required
def actions_compare_data(request):
    """Отображает страницу создания кампании"""
    page_name = 'Соответствие акций'
    ur_lico_data = UrLico.objects.all()
    
    ur_lico = UrLico.objects.get(ur_lice_name="ООО Иннотрейд")
    action_list = Action.objects.filter(ur_lico=ur_lico, marketplace__id=1)
    action_obj = Action.objects.filter(ur_lico=ur_lico, date_finish__gt=datetime.now()).order_by('-id').first()
    articles_data = ArticleInActionWithCondition.objects.filter(article__company=ur_lico.ur_lice_name, wb_action__action_number=1)
  
    if request.POST:
        if 'ur_lico_select' in request.POST and 'action_select' in request.POST:
            ur_lico_obj = UrLico.objects.get(id=int(request.POST.get('ur_lico_select')))
            action_obj = Action.objects.get(id=int(request.POST.get('action_select')))
            articles_data = ArticleInActionWithCondition.objects.filter(article__company=ur_lico_obj.ur_lice_name, wb_action=action_obj)
    main_data = []
    if articles_data:
        for dat in articles_data:
            inner_list = []
            inner_list.append(dat.article.common_article)
            inner_list.append(dat.article.maybe_in_action.filter(action=dat.wb_action).first().action_price)
            inner_list.append(dat.ozon_action_id.name)
            inner_list.append(dat.article.maybe_in_action.filter(action=dat.ozon_action_id).first().action_price)
            inner_list.append(dat.id)
            main_data.append(inner_list)
    context = {
        'page_name': page_name,
        'ur_lico_data': ur_lico_data,
        'main_data': main_data,
        'action_list': action_list,
        'accept_conditions': len(main_data),
        'common_amount': action_obj.articles_amount,
        'date_finish': action_obj.date_finish,
       
    }
    return render(request, 'actions/action_list.html', context)



# ========== ДЛЯ AJAX ЗАПРОСОВ ========= #
def get_actions(request):
    """Для AJAX запроса. Показывает список акций в зависимсоти от выбора Юр лица"""
    ur_lico_id = request.GET.get('ur_lico_id')
    actions = Action.objects.filter(ur_lico_id=ur_lico_id, marketplace__id=1).values('id', 'name')  # замените 'name' на нужное поле
    actions_list = list(actions)
    return JsonResponse(actions_list, safe=False)


def add_to_action(request):
    """Для AJAX запроса. Добавляет выбранные артикулы в акции"""
    if request.POST:
        print(request.POST)
        # raw_articles_list = request.POST.get('articles')
        # article_list = raw_articles_list.split(',')
        # for article in article_list:
        #     Articles.objects.get(id=int(article)).delete()
    return JsonResponse({'message': 'Value saved successfully.'})