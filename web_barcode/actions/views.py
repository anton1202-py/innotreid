import ast
from datetime import datetime
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render

from reklama.models import UrLico
from actions.models import Action, ArticleInAction, ArticleInActionWithCondition, ArticleMayBeInAction
from actions.supplyment import add_articles_to_wb_action, create_data_with_article_conditions, del_articles_from_ozon_action, del_articles_from_wb_action, save_articles_added_to_action, sender_message_about_articles_in_action_already, wb_auto_action_article_price_excel_import
from api_request.ozon_requests import add_ozon_articles_to_action
from api_request.wb_requests import add_wb_articles_to_action
from actions.periodic_tasks import add_new_actions_ozon_to_db
from web_barcode.constants_file import header_wb_dict, header_ozon_dict, bot
from price_system.models import Articles

@login_required
def actions_compare_data(request):
    """Отображает страницу создания кампании"""
    page_name = 'Соответствие акций'
    ur_lico_data = UrLico.objects.all()
    user_chat_id = request.user.tg_chat_id
    ur_lico_obj = UrLico.objects.get(ur_lice_name="ООО Иннотрейд")

    action_obj = Action.objects.filter(ur_lico=ur_lico_obj, date_finish__gt=timezone.make_aware(datetime.now())).order_by('-id').first()
    articles_data = ArticleInActionWithCondition.objects.filter(article__company=ur_lico_obj.ur_lice_name, wb_action__action_number=1)
    percent_condition = ''

    import_data= ''
    if request.POST:
        print(request.POST)
        if 'ur_lico_select' in request.POST and 'action_select' in request.POST:
            ur_lico_obj = UrLico.objects.get(id=int(request.POST.get('ur_lico_select')))
            action_obj = Action.objects.get(id=int(request.POST.get('action_select')))
            articles_data = ArticleInActionWithCondition.objects.filter(wb_action=action_obj)

        if 'import_file' in request.FILES:
            ur_lico_obj = UrLico.objects.get(id=int(request.POST.get('ur_lico_obj')))
            action_obj = Action.objects.get(id=int(request.POST.get('action_obj')))
            import_data = wb_auto_action_article_price_excel_import(
                request.FILES['import_file'], ur_lico_obj.ur_lice_name, action_obj)
            # Сопоставляем для акции ВБ товары из акций Озон.
            create_data_with_article_conditions(action_obj, user_chat_id)
            if type(import_data) != str:
                return redirect('actions_compare_data')
        if 'percent_submitBtn' in request.POST:
            ur_lico_obj = UrLico.objects.get(id=int(request.POST.get('percent_ur_lico')))
            action_obj = Action.objects.get(id=int(request.POST.get('percent_action')))
            if request.POST.get('differrence_percent'):
                percent_condition = int(request.POST.get('differrence_percent'))
            else:
                percent_condition = None
            ArticleInActionWithCondition.objects.filter(article__company=ur_lico_obj.ur_lice_name, wb_action=action_obj).delete()
            create_data_with_article_conditions(action_obj, user_chat_id, percent_condition=percent_condition)
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
    action_list = Action.objects.filter(ur_lico=ur_lico_obj, marketplace__id=1, date_finish__gt=timezone.make_aware(datetime.now()))
    context = {
        'user_chat_id': user_chat_id,
        'page_name': page_name,
        'ur_lico_data': ur_lico_data,
        'main_data': main_data,
        'action_list': action_list,
        'action_obj': action_obj,
        'ur_lico_obj': ur_lico_obj,
        'percent_condition': percent_condition,
        'accept_conditions': len(main_data),
        'action_name': action_obj.name,
        'common_amount': len(ArticleMayBeInAction.objects.filter(action=action_obj)),
        'date_finish': action_obj.date_finish,
        'date_start': action_obj.date_start,
       
    }
    return render(request, 'actions/action_list.html', context)


@login_required
def article_in_actions(request):
    """Отображает страницу товаров в акциях. Выход из акций."""
    page_name = 'Товары в акциях'
    ur_lico_data = UrLico.objects.all()
    user_chat_id = request.user.tg_chat_id
    ur_lico_obj = UrLico.objects.get(ur_lice_name="ООО Иннотрейд")
    
    action_obj = Action.objects.filter(ur_lico=ur_lico_obj, date_finish__gt=timezone.make_aware(datetime.now())).order_by('-id').first()
    actions_data = ArticleInAction.objects.filter(article__company=ur_lico_obj.ur_lice_name, action__action_number=1)
    import_data= ''
    
    if request.POST:
        if 'ur_lico_select' in request.POST and 'action_select' in request.POST:
            ur_lico_obj = UrLico.objects.get(id=int(request.POST.get('ur_lico_select')))
            action_obj = Action.objects.get(id=int(request.POST.get('action_select')))
            articles_data = ArticleInActionWithCondition.objects.filter(article__company=ur_lico_obj.ur_lice_name, wb_action=action_obj)
        if 'import_file' in request.FILES:
            ur_lico_obj = UrLico.objects.get(id=int(request.POST.get('ur_lico_obj')))
            action_obj = Action.objects.get(id=int(request.POST.get('action_obj')))
            import_data = wb_auto_action_article_price_excel_import(
                request.FILES['import_file'], ur_lico_obj.ur_lice_name, action_obj)
            # Сопоставляем для акции ВБ товары из акций Озон.
            create_data_with_article_conditions(action_obj)
            if type(import_data) != str:
                return redirect('actions_compare_data')
        
        
    articles_list = list(ArticleInAction.objects.filter(article__company=ur_lico_obj.ur_lice_name, action=action_obj).values_list('article', flat=True))
    
    articles_in_ozon_actions = ArticleInAction.objects.filter(action__marketplace=2, article__in=articles_list, date_finish__isnull=True).order_by('article__common_article')
    action_list = Action.objects.filter(ur_lico=ur_lico_obj, marketplace__id=1, date_finish__gt=timezone.make_aware(datetime.now()))
    context = {
        'user_chat_id': user_chat_id,
        'page_name': page_name,
        'ur_lico_obj': ur_lico_obj,
        'actions_data': actions_data,
        'articles_in_ozon_actions': articles_in_ozon_actions,
        'ur_lico_data': ur_lico_data,
        'action_list': action_list,
        'action_obj': action_obj.id,
        'action_name': action_obj.name,
        'common_amount': len(ArticleMayBeInAction.objects.filter(action=action_obj)),
        'in_action_amount': len(ArticleInAction.objects.filter(action__marketplace=2, article__in=articles_list, date_finish__isnull=True)),
        'date_finish': action_obj.date_finish,
        'date_start': action_obj.date_start,
       
    }
    return render(request, 'actions/article_in_actions.html', context)



# ========== ДЛЯ AJAX ЗАПРОСОВ ========= #
def get_actions(request):
    """Для AJAX запроса. Показывает список акций в зависимости от выбора Юр лица"""
    ur_lico_id = request.GET.get('ur_lico_id')
    print('ur_lico_id', ur_lico_id)
    actions = Action.objects.filter(ur_lico__id=ur_lico_id, marketplace__id=1, date_finish__gt=timezone.make_aware(datetime.now())).values('id', 'name')
    actions_list = list(actions)
    return JsonResponse(actions_list, safe=False)


def add_to_action(request):
    """Для AJAX запроса. Добавляет выбранные артикулы в акции"""
    if request.POST:
        raw_articles_conditions = request.POST.get('articles')
        articles_conditions = raw_articles_conditions.split(',')
        user_chat_id = request.POST.get('user_chat_id')
        wb_articles_price_dict = {}
        wb_article_obj_list = []
        wb_action_obj = ''
        ozon_actions_data = {}
        ozon_for_save_in_db_actions_data = {}
        wb_action_number = 0
        wb_action_name = ''
        common_message = {}
        if articles_conditions:
            ur_lico = ''
            for article in articles_conditions:
                if article:
                    article_in_action_obj = ArticleInActionWithCondition.objects.get(id=int(article))
                    wb_action_obj = article_in_action_obj.wb_action
                    wb_price = article_in_action_obj.article.maybe_in_action.filter(action=wb_action_obj).first().action_price
                    ur_lico = article_in_action_obj.article.company
                    wb_action_name = article_in_action_obj.wb_action.name

                    wb_articles_price_dict[article_in_action_obj.article] = wb_price
                    wb_article_obj_list.append(article_in_action_obj.article)
                    
                    wb_action_number = int(article_in_action_obj.wb_action.action_number)
                    if article_in_action_obj.ozon_action_id.action_number in ozon_actions_data:
                        ozon_actions_data[article_in_action_obj.ozon_action_id.action_number].append(
                            {
                                "action_price": article_in_action_obj.article.maybe_in_action.filter(action=article_in_action_obj.ozon_action_id).first().action_price,
                                "product_id": article_in_action_obj.article.ozon_product_id,
                                "stock": 10
                            }
                        )
                        ozon_for_save_in_db_actions_data[article_in_action_obj.ozon_action_id].append(article_in_action_obj.article)
                    else:
                        ozon_actions_data[article_in_action_obj.ozon_action_id.action_number]= [
                            {
                                "action_price": article_in_action_obj.article.maybe_in_action.filter(action=article_in_action_obj.ozon_action_id).first().action_price,
                                "product_id": article_in_action_obj.article.ozon_product_id,
                                "stock": 10
                            }
                        ]
                        ozon_for_save_in_db_actions_data[article_in_action_obj.ozon_action_id] = [article_in_action_obj.article]
            ozon_header = header_ozon_dict[ur_lico]
            

            # Сохраняем в нашу базу данных информацию какой артикул в какую акцию добавляется
            wb_message = save_articles_added_to_action(wb_article_obj_list, wb_action_obj)
            common_ozon_message = []
            for ozon_action, article_list in ozon_for_save_in_db_actions_data.items():
                ozon_message = save_articles_added_to_action(article_list, ozon_action)
                if ozon_message:
                    common_ozon_message.append(ozon_message)

            # TODO размьютить код для добавления в акцию на МП   
            add_articles_to_wb_action(ur_lico, wb_articles_price_dict)
            for ozon_action, article_list in ozon_actions_data.items():
                add_ozon_articles_to_action(ozon_header, ozon_action, article_list)

            message = f'Добавил в акцию ВБ {wb_action_name}: {len(wb_articles_price_dict.keys())} артикулов'
            bot.send_message(chat_id=user_chat_id,
                             text=message[:4000])
            if wb_message and common_ozon_message:
                common_message = {'wb': wb_message, 'ozon': common_ozon_message}
                sender_message_about_articles_in_action_already(user_chat_id, common_message)
    return JsonResponse({'message': 'Value saved successfully.'})


def del_from_action(request):
    """Для AJAX запроса. Удаляет выбранные артикулы из акций"""

    if request.POST:
        raw_articles_conditions = request.POST.get('articles')
        article_in_ozon_actions_list = []
        articles_conditions = raw_articles_conditions.split(',')
        for i in articles_conditions:
            new_text = i.replace(';', ',')
            dictionary = ast.literal_eval(new_text)
            article_in_ozon_actions_list.append(dictionary)
        user_chat_id = request.POST.get('user_chat_id')
        wb_action_id = request.POST.get('wb_action')
        ur_lico_name = request.POST.get('ur_lico_name')

        for_wb_exit_list = []
        for_ozon_exit_dict = {}
        for data in article_in_ozon_actions_list:
            article_obj = Articles.objects.get(id=data['article'])
            for_wb_exit_list.append(article_obj)

            ozon_action_obj = Action.objects.get(id=data['action'])
            if ozon_action_obj in for_ozon_exit_dict:
                for_ozon_exit_dict[ozon_action_obj].append(article_obj.ozon_product_id)
            else:
                for_ozon_exit_dict[ozon_action_obj] = [article_obj.ozon_product_id]
        print('for_wb_exit_list', for_wb_exit_list)
        print('wb_action_id', wb_action_id)
        # Удаляем артикулы из акции ВБ
        del_articles_from_wb_action(for_wb_exit_list, wb_action_id, user_chat_id)

        # Удаляем артикулы из акции Озон
        del_articles_from_ozon_action(for_ozon_exit_dict, ur_lico_name, user_chat_id)
        
    return JsonResponse({'message': 'Value saved successfully.'})