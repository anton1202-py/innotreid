from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from reklama.models import UrLico
from actions.models import Action, ArticleInActionWithCondition
from api_request.wb_requests import add_wb_articles_to_action


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
        raw_articles_conditions = request.POST.get('articles')
        articles_conditions = raw_articles_conditions.split(',')
        wb_articles_list = []
        wb_action_number = 0
        if articles_conditions:
            for article in articles_conditions:
                if article:
                    article_in_action_obj = ArticleInActionWithCondition.objects.get(id=int(article))
                    wb_articles_list.append(article_in_action_obj.article.wb_nomenclature)
                    wb_action_number = article_in_action_obj.wb_action.action_number
                    print(wb_action_number)
            print(wb_articles_list)
            # add_wb_articles_to_action(header, wb_action_number, wb_articles_list)
    return JsonResponse({'message': 'Value saved successfully.'})