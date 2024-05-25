import ast
import os
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Max, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from dotenv import load_dotenv
from motivation.models import DesignerReward, Selling
from motivation.supplyment import (articles_data_merge, get_current_selling,
                                   motivation_article_type_excel_file_export,
                                   motivation_article_type_excel_import)
from price_system.models import Articles, DesignUser
from users.models import InnotreidUser

from .forms import UploadFileForm


def get_main_sales_data():
    """Отдает данные по продажам артикулов"""
    sale_data = Selling.objects.all().values('lighter', 'month', 'quantity')
    # Словарь с данными артикула по продажам по месяцам
    main_sales_dict = {}
    # Словарь с продажами артикула за текущий год
    year_sales_dict = {}
    for data in sale_data:
        if data['lighter'] in main_sales_dict:
            if data['month'] in main_sales_dict[data['lighter']]:
                main_sales_dict[data['lighter']
                                ][data['month']] += int(data['quantity'])
            else:
                main_sales_dict[data['lighter']
                                ][data['month']] = int(data['quantity'])
        else:
            main_sales_dict[data['lighter']] = {
                data['month']: int(data['quantity'])}
        if data['lighter'] in year_sales_dict:
            year_sales_dict[data['lighter']] += int(data['quantity'])
        else:
            year_sales_dict[data['lighter']] = int(data['quantity'])
    return year_sales_dict, main_sales_dict


def get_designers_sales_data():
    """Отдает данные по продажам дизайнеров"""
    sale_data = Selling.objects.all().values(
        'lighter', 'month', 'summ', 'lighter__designer')
    print(sale_data)
    designer_rew_dict = {}
    designer_persent = DesignUser.objects.all().values(
        'designer', 'main_reward_persent', 'copyright_reward_persent')
    for i in designer_persent:
        if i['copyright_reward_persent']:
            designer_rew_dict[i['designer']] = i['copyright_reward_persent']
        elif not i['copyright_reward_persent'] and i['main_reward_persent']:
            designer_rew_dict[i['designer']] = i['main_reward_persent']
        else:
            designer_rew_dict[i['designer']] = 0
    print(designer_rew_dict)
    # Словарь с данными артикула по продажам по месяцам
    monthly_sales_dict = {}
    # Словарь с продажами артикула за текущий год
    year_sales_dict = {}
    for data in sale_data:
        if data['lighter__designer']:
            if data['lighter__designer'] in monthly_sales_dict:
                if data['month'] in monthly_sales_dict[data['lighter__designer']]:
                    monthly_sales_dict[data['lighter__designer']
                                       ][data['month']] += int(data['summ']*designer_rew_dict[data['lighter__designer']]/100)
                else:
                    monthly_sales_dict[data['lighter__designer']
                                       ][data['month']] = int(data['summ']*designer_rew_dict[data['lighter__designer']]/100)
            else:
                monthly_sales_dict[data['lighter__designer']] = {
                    data['month']: int(data['summ']*designer_rew_dict[data['lighter__designer']]/100)}
            if data['lighter__designer'] in year_sales_dict:
                year_sales_dict[data['lighter__designer']
                                ] += int(data['summ']*designer_rew_dict[data['lighter__designer']]/100)
            else:
                year_sales_dict[data['lighter__designer']] = int(
                    data['summ']*designer_rew_dict[data['lighter__designer']]/100)
    return year_sales_dict, monthly_sales_dict


def article_designers(request):
    """Отображает артикулы дизайнеров"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    # get_current_selling()
    current_year = datetime.now().strftime('%Y')
    page_name = 'Светильники дизайнеров'
    article_list = Articles.objects.filter(
        designer_article=True).order_by('common_article')
    sale_data = Selling.objects.all().values('lighter', 'month', 'summ')

    # Проверяю наличия данных из формы фильтра юр лица.
    months = Selling.objects.filter(
        year=current_year).values('month').distinct()
    month_list = [int(value['month']) for value in months]

    year_sales_dict, main_sales_dict = get_main_sales_data()

    # Получаем список пользователей из группы "Дизайнеры"
    designer_group = Group.objects.get(name='Дизайнеры')
    designer_list = designer_group.user_set.all()

    if request.POST:
        filter_company = request.POST.get('filter_data')
        common_article = request.POST.get("common_article")
        designer = request.POST.get("designer")
        # if filter_company:
        #     article_list = Articles.objects.filter(
        #         company=filter_company).order_by('common_article')
        # request.session['filter_data'] = request.POST.get('filter_data')
        if common_article:
            article_list = Articles.objects.filter(
                Q(common_article=common_article)).order_by('common_article')
            # request.session['common_article'] = request.POST.get(
            #     'common_article')
        if designer:
            article_list = Articles.objects.filter(
                Q(designer=designer)).order_by('common_article')
            # request.session['designer'] = request.POST.get('designer')

        # return redirect('motivation_article_designers')

    context = {
        'page_name': page_name,
        'article_list': article_list,
        'year_sales_dict': year_sales_dict,
        'designer_list': designer_list,
        'month_list': sorted(month_list),
        'main_sales_dict': main_sales_dict,
        'current_year': current_year
    }
    return render(request, 'motivation/article_designers.html', context)


def update_model_field(request):

    if request.method == 'POST':
        # Сохраняем значение в базу данных
        user_id = request.POST.get('selected_designer')
        article = request.POST.get('article')
        if user_id:
            user_obj = InnotreidUser.objects.get(id=int(user_id))
            Articles.objects.filter(common_article=article).update(
                designer=user_obj)
        else:
            Articles.objects.filter(common_article=article).update(
                designer=None)
        return JsonResponse({'message': 'Value saved successfully.'})
    return JsonResponse({'error': 'Invalid request method.'}, status=400)


def filter_get_request(request, ur_lico):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        search_term = request.GET.get('search_term', None)
        article_list = Articles.objects.filter(
            common_article__contains=search_term)
        if search_term:
            filtered_articles = Articles.objects.filter(company=ur_lico,
                                                        common_article__contains=search_term).order_by('common_article')
        else:
            filtered_articles = Articles.objects.filter(
                company=ur_lico).order_by('common_article')
        data = [{'common_article': article.common_article,
                'designer_article': article.designer_article,
                 'copy_right': article.copy_right} for article in filtered_articles]
        return JsonResponse(data, safe=False)


def filter_get_delete_request(request):
    """Показывает таблицу при удалении артикулов из строки фильтра"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        search_term = request.GET.get('search_term', None)
        if search_term:
            filtered_articles = Articles.objects.filter(
                common_article__contains=search_term)
            data = [{'common_article': article.common_article,
                     'designer_article': article.designer_article,
                     'copy_right': article.copy_right} for article in filtered_articles]
        else:
            filtered_articles = Articles.objects.all()
            data = [{'common_article': article.common_article,
                     'designer_article': article.designer_article,
                     'copy_right': article.copy_right} for article in filtered_articles]
        return JsonResponse(data, safe=False)


def article_type(request):
    """
    Отображает тип светильника:
    дизайнерский или нет, с правами собственности или нет.
    """
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = 'Тип светильника'

    ur_lico = 'ООО Иннотрейд'
    if 'filter_data' in request.session:
        ur_lico = request.session['filter_data']
    article_list = Articles.objects.filter(company=ur_lico).order_by('common_article').values(
        'common_article', 'company', 'designer_article', 'copy_right')
    import_data = ''
    if request.GET:
        return filter_get_request(request, ur_lico)

    if request.POST:
        filter_company = request.POST.get('filter_data')
        if filter_company:
            article_list = Articles.objects.filter(
                company=filter_company).order_by('common_article').values(
                'common_article', 'company', 'designer_article', 'copy_right')
            request.session['filter_data'] = request.POST.get('filter_data')
        if 'export' in request.POST or 'import_file' in request.FILES:
            if request.POST.get('export') == 'create_file':

                return motivation_article_type_excel_file_export(article_list)

            elif 'import_file' in request.FILES:
                import_data = motivation_article_type_excel_import(
                    request.FILES['import_file'], ur_lico)
                if type(import_data) == str:
                    print('Ошибочка')
                else:
                    return redirect('motivation_article_type')
        if 'common_article' in request.POST:
            filter_data = request.POST
            article_filter = filter_data.get("common_article")
            article_list = Articles.objects.filter(company=ur_lico, common_article__contains=article_filter).order_by('common_article').values(
                'common_article', 'company', 'designer_article', 'copy_right')

    context = {
        'page_name': page_name,
        'article_list': article_list,
        'import_data': import_data
    }
    return render(request, 'motivation/article_type.html', context)


def update_article_designer_boolean_field(request):
    if request.method == 'POST':

        # Сохраняем значение в базу данных
        article_type = request.POST.get('designer_article_type')
        article = request.POST.get('article')
        checkbox_value = not ast.literal_eval(article_type)
        Articles.objects.filter(common_article=article).update(
            designer_article=checkbox_value)

        return JsonResponse({'message': 'Value saved successfully.'})
    return JsonResponse({'error': 'Invalid request method.'}, status=400)


def update_article_copyright_boolean_field(request):
    if request.method == 'POST':

        # Сохраняем значение в базу данных
        copyright_type = request.POST.get('copyright_article_type')
        article = request.POST.get('article')
        checkbox_value = not ast.literal_eval(copyright_type)
        Articles.objects.filter(common_article=article).update(
            copy_right=checkbox_value)

        return JsonResponse({'message': 'Value saved successfully.'})
    return JsonResponse({'error': 'Invalid request method.'}, status=400)


def designers_rewards(request):
    """Отображает страницы с вознаграждением дизайнеров"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = 'Вознаграждение дизайнеров'
    current_year = datetime.now().strftime('%Y')
    # Список месяцев в текущем году
    months = Selling.objects.filter(
        year=current_year).values('month').distinct()
    month_list = [int(value['month']) for value in months]

    sale_data = Selling.objects.all().values(
        'lighter', 'month', 'summ', 'lighter__designer')
    designer_main_percent = DesignUser.objects.values(
        'designer__id', 'main_reward_persent', 'copyright_reward_persent')
    designer_percent = {}
    for data in designer_main_percent:
        if data['main_reward_persent']:
            if data['copyright_reward_persent']:
                designer_percent[data['designer__id']
                                 ] = data['copyright_reward_persent']/100
            else:
                designer_percent[data['designer__id']
                                 ] = data['main_reward_persent']/100

    print('designer_percent', designer_percent)
    year_sales_dict, monthly_sales_dict = get_designers_sales_data()
    print('year_sales_dict', year_sales_dict)
    # Находим группу "Дизайнеры"
    designer_group = Group.objects.get(name='Дизайнеры')

    # Получаем список пользователей из группы "Дизайнер"
    designer_users = designer_group.user_set.all()

    context = {
        'page_name': page_name,
        'designer_users': designer_users,
        'sale_data': sale_data,
        'monthly_sales_dict': monthly_sales_dict,
        'designer_percent': designer_percent,
        'year_sales_dict': year_sales_dict,
        'month_list': sorted(month_list),
        'current_year': current_year,

    }
    return render(request, 'motivation/designers_reward.html', context)


def percent_designers_rewards(request):
    """Отображает страницу с процентами награждения каждого дизайнера"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = 'Процент вознаграждения'
    percent_data = DesignUser.objects.all().order_by('designer__last_name')
    print(percent_data[0])
    for el in percent_data:
        print(el.main_reward_persent)
        print(el.copyright_reward_persent)
    if request.GET:
        print('Попал в фильтр')
    context = {
        'page_name': page_name,
        'percent_data': percent_data
    }
    return render(request, 'motivation/percent_reward.html', context)


def update_percent_reward(request):
    if request.method == 'POST':
        designer = request.POST.get('designer')
        # Сохраняем значение % за авторство в базу данных
        if 'main_percent' in request.POST:
            main_persent = request.POST.get('main_percent')
            DesignUser.objects.filter(designer__username=designer).update(
                main_reward_persent=main_persent
            )
        # Сохраняем значение % за интелектуальное право в базу данных
        if 'copyright_percent' in request.POST:
            copyright_persent = request.POST.get('copyright_percent')
            DesignUser.objects.filter(designer__username=designer).update(
                copyright_reward_persent=copyright_persent
            )
        return JsonResponse({'message': 'Value saved successfully.'})
    return JsonResponse({'error': 'Invalid request method.'}, status=400)
