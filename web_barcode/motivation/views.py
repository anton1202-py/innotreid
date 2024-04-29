import os
from datetime import datetime

from django.db.models import Max, Q
from django.shortcuts import redirect, render
from dotenv import load_dotenv
from motivation.models import DesignerReward, DesignUser, Lighters, Selling
from motivation.supplyment import articles_data_merge, designer_data_merge
from price_system.models import Articles

from .forms import DesignerChooseForm


def article_designers(request):
    """Отображает список рекламных компаний WB и добавляет их"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    # designer_data_merge()
    page_name = 'Светильники дизайнеров'
    article_list = Lighters.objects.all()
    sale_data = Selling.objects.all()
    form = DesignerChooseForm()
    context = {
        'page_name': page_name,
        'article_list': article_list,
        'sale_data': sale_data,
        'form': form
    }
    return render(request, 'motivation/article_designers.html', context)


def article_sale(request):
    """Отображает список рекламных компаний WB и добавляет их"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = 'Продажи светильников'
    article_list = Lighters.objects.all()
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
    article_list = Lighters.objects.all()
    sale_data = Selling.objects.all()

    context = {
        'page_name': page_name,
        'article_list': article_list,
        'sale_data': sale_data
    }
    return render(request, 'motivation/article_designers.html', context)
