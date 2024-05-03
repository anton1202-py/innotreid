import os
from datetime import datetime

from django.contrib.auth.models import Group, User
from django.db.models import Max, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from dotenv import load_dotenv
from motivation.models import DesignerReward, Selling
from motivation.supplyment import articles_data_merge, designer_data_merge
from price_system.models import Articles, DesignUser

from .forms import DesignerChooseForm


def article_designers(request):
    """Отображает список рекламных компаний WB и добавляет их"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    # designer_data_merge()
    page_name = 'Светильники дизайнеров'
    article_list = Articles.objects.filter(
        company='ООО Иннотрейд').order_by('common_article')
    sale_data = Selling.objects.all()
    designer_group = Group.objects.get(name='Дизайнеры')
    # Получаем список пользователей из группы "Дизайнеры"
    designer_list = designer_group.user_set.all()
    form = DesignerChooseForm()

    if request.POST:
        if 'filter_data' in request.POST:
            filter_company = request.POST.get('filter_data')
            article_list = Articles.objects.filter(
                company=filter_company).order_by('common_article')
        elif 'designer_save' in request.POST:
            user_id = request.POST.get('designer_name')
            article = request.POST.get('designer_save')
            user_obj = User.objects.get(id=user_id)
            Articles.objects.filter(common_article=article).update(
                designer=user_obj)
            print(request.POST)

    context = {
        'page_name': page_name,
        'article_list': article_list,
        'sale_data': sale_data,
        'designer_list': designer_list,
        'form': form
    }
    return render(request, 'motivation/article_designers.html', context)


def update_model_field(request):
    if request.method == 'POST':
        # Сохраняем значение в базу данных
        user_id = request.POST.get('selected_designer')
        article = request.POST.get('article')
        user_obj = User.objects.get(id=int(user_id))
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
    article_list = User.objects.all()
    sale_data = Selling.objects.all()

    # Находим группу "Дизайнер"
    designer_group = Group.objects.get(name='Дизайнеры')

    # Получаем список пользователей из группы "Дизайнер"
    designer_users = designer_group.user_set.all()
    print(designer_users)

    context = {
        'page_name': page_name,
        'designer_users': designer_users,
        'sale_data': sale_data
    }
    return render(request, 'motivation/designers_reward.html', context)
