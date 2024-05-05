import os
from datetime import datetime

from django.contrib.auth.models import Group
from django.db.models import Max, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from dotenv import load_dotenv
from motivation.models import DesignerReward, Selling
from motivation.supplyment import (articles_data_merge, designer_data_merge,
                                   get_current_selling)
from price_system.models import Articles, DesignUser
from users.models import InnotreidUser

from .forms import DesignerChooseForm


def get_main_sales_data():
    """Отдает данные по продажам артикулов"""
    sale_data = Selling.objects.all().values('lighter', 'month', 'summ')
    # Словарь с данными артикула по продажам по месяцам
    main_sales_dict = {}
    # Словарь с продажами артикула за текущий год
    year_sales_dict = {}
    for data in sale_data:
        if data['lighter'] in main_sales_dict:
            if data['month'] in main_sales_dict[data['lighter']]:
                main_sales_dict[data['lighter']
                                ][data['month']] += int(data['summ'])
            else:
                main_sales_dict[data['lighter']
                                ][data['month']] = int(data['summ'])
        else:
            main_sales_dict[data['lighter']] = {
                data['month']: int(data['summ'])}
        if data['lighter'] in year_sales_dict:
            year_sales_dict[data['lighter']] += int(data['summ'])
        else:
            year_sales_dict[data['lighter']] = int(data['summ'])
    return year_sales_dict, main_sales_dict


def get_designers_sales_data():
    """Отдает данные по продажам дизайнеров"""
    sale_data = Selling.objects.all().values(
        'lighter', 'month', 'summ', 'lighter__designer')
    # Словарь с данными артикула по продажам по месяцам
    monthly_sales_dict = {}
    # Словарь с продажами артикула за текущий год
    year_sales_dict = {}
    for data in sale_data:
        if data['lighter__designer'] in monthly_sales_dict:
            if data['month'] in monthly_sales_dict[data['lighter__designer']]:
                monthly_sales_dict[data['lighter__designer']
                                   ][data['month']] += int(data['summ'])
            else:
                monthly_sales_dict[data['lighter__designer']
                                   ][data['month']] = int(data['summ'])
        else:
            monthly_sales_dict[data['lighter__designer']] = {
                data['month']: int(data['summ'])}
        if data['lighter__designer'] in year_sales_dict:
            year_sales_dict[data['lighter__designer']] += int(data['summ'])
        else:
            year_sales_dict[data['lighter__designer']] = int(data['summ'])
    return year_sales_dict, monthly_sales_dict


def article_designers(request):
    """Отображает список рекламных компаний WB и добавляет их"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    get_current_selling()

    current_year = datetime.now().strftime('%Y')
    page_name = 'Светильники дизайнеров'
    article_list = Articles.objects.filter(
        company='ООО Иннотрейд').order_by('common_article')
    sale_data = Selling.objects.all().values('lighter', 'month', 'summ')

    # Проверяю наличия данных из формы фильтра юр лица.
    filter_data = request.session.get('filter_data')
    if filter_data:
        article_list = Articles.objects.filter(
            company=filter_data).order_by('common_article')

    # Список месяцев в текущем году
    months = Selling.objects.filter(
        year=current_year).values('month').distinct()
    month_list = [int(value['month']) for value in months]

    year_sales_dict, main_sales_dict = get_main_sales_data()

    # Получаем список пользователей из группы "Дизайнеры"
    designer_group = Group.objects.get(name='Дизайнеры')
    designer_list = designer_group.user_set.all()

    if request.POST:
        if 'filter_data' in request.POST:
            filter_company = request.POST.get('filter_data')
            article_list = Articles.objects.filter(
                company=filter_company).order_by('common_article')
            request.session['filter_data'] = request.POST.get('filter_data')
        return redirect('motivation_article_designers')

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
        user_obj = InnotreidUser.objects.get(id=int(user_id))
        Articles.objects.filter(common_article=article).update(
            designer=user_obj)
        return JsonResponse({'message': 'Value saved successfully.'})
    return JsonResponse({'error': 'Invalid request method.'}, status=400)


def article_sale(request):
    """Отображает список рекламных компаний WB и добавляет их"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = 'Продажи светильников'
    article_list = Articles.objects.all()
    sale_data = Selling.objects.all()

    context = {
        'page_name': page_name,
        'article_list': article_list,
        'sale_data': sale_data
    }
    return render(request, 'motivation/article_designers.html', context)


def designers_rewards(request):
    """Отображает список рекламных компаний WB и добавляет их"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = 'Вознаграждение дизайнеров'
    current_year = datetime.now().strftime('%Y')
    # Список месяцев в текущем году
    months = Selling.objects.filter(
        year=current_year).values('month').distinct()
    month_list = [int(value['month']) for value in months]

    page_name = 'Вознаграждение дизайнеров'

    sale_data = Selling.objects.all().values(
        'lighter', 'month', 'summ', 'lighter__designer')

    year_sales_dict, monthly_sales_dict = get_designers_sales_data()

    # Находим группу "Дизайнеры"
    designer_group = Group.objects.get(name='Дизайнеры')

    # Получаем список пользователей из группы "Дизайнер"
    designer_users = designer_group.user_set.all()

    context = {
        'page_name': page_name,
        'designer_users': designer_users,
        'sale_data': sale_data,
        'monthly_sales_dict': monthly_sales_dict,
        'year_sales_dict': year_sales_dict,
        'month_list': sorted(month_list),
        'current_year': current_year,

    }
    return render(request, 'motivation/designers_reward.html', context)
