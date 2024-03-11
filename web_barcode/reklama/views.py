import importlib
import json
import os
from datetime import datetime, timedelta

import requests
from django.db.models import F, Max, Q
from django.shortcuts import redirect, render
from django.views.generic import DeleteView, DetailView, ListView, UpdateView
from dotenv import load_dotenv
from reklama.forms import FilterUrLicoForm
from reklama.models import (AdvertisingCampaign, CompanyStatistic,
                            ProcentForAd, SalesArticleStatistic, UrLico,
                            WbArticleCommon, WbArticleCompany)
from reklama.periodic_tasks import create_articles_company, header_determinant

dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)


API_KEY_WB_IP = os.getenv('API_KEY_WB_IP')
YANDEX_IP_KEY = os.getenv('YANDEX_IP_KEY')
API_KEY_OZON_KARAVAEV = os.getenv('API_KEY_OZON_KARAVAEV')
CLIENT_ID_OZON_KARAVAEV = os.getenv('CLIENT_ID_OZON_KARAVAEV')

OZON_OOO_API_TOKEN = os.getenv('OZON_OOO_API_TOKEN')
OZON_OOO_CLIENT_ID = os.getenv('OZON_OOO_CLIENT_ID')
YANDEX_OOO_KEY = os.getenv('YANDEX_OOO_KEY')
WB_OOO_API_KEY = os.getenv('WB_OOO_API_KEY')


TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID_ADMIN = os.getenv('CHAT_ID_ADMIN')
CHAT_ID_MANAGER = os.getenv('CHAT_ID_MANAGER')
CHAT_ID_EU = os.getenv('CHAT_ID_EU')
CHAT_ID_AN = os.getenv('CHAT_ID_AN')

wb_headers_karavaev = {
    'Content-Type': 'application/json',
    'Authorization': API_KEY_WB_IP
}
wb_headers_ooo = {
    'Content-Type': 'application/json',
    'Authorization': WB_OOO_API_KEY
}

ozon_headers_karavaev = {
    'Api-Key': API_KEY_OZON_KARAVAEV,
    'Content-Type': 'application/json',
    'Client-Id': CLIENT_ID_OZON_KARAVAEV
}
ozon_headers_ooo = {
    'Api-Key': OZON_OOO_API_TOKEN,
    'Content-Type': 'application/json',
    'Client-Id': OZON_OOO_CLIENT_ID
}

yandex_headers_karavaev = {
    'Authorization': YANDEX_IP_KEY,
}
yandex_headers_ooo = {
    'Authorization': YANDEX_OOO_KEY,
}


def ad_campaign_add(request):
    """Отображает список рекламных компаний и добавляет их"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    company_list = AdvertisingCampaign.objects.all()
    koef_campaign_data = ProcentForAd.objects.values('campaign_number').annotate(
        latest_add=Max('id')).values('campaign_number', 'latest_add', 'koef_date', 'koefficient')
    koef_dict = {}
    for koef in koef_campaign_data:
        koef_dict[koef['campaign_number']] = [
            koef['koefficient'], koef['koef_date'], koef['latest_add']]
    form = FilterUrLicoForm()
    if request.POST:
        request_data = request.POST
        if 'add_button' in request.POST:
            ur_lico_obj = UrLico.objects.get(id=request_data['ur_lico_name'])
            obj, created = AdvertisingCampaign.objects.get_or_create(
                campaign_number=request_data['campaign_number'],
                ur_lico=ur_lico_obj
            )
            koef_obj, korf_created = ProcentForAd.objects.get_or_create(
                campaign_number=obj,
                koefficient=int(request_data['ad_koefficient'])
            )
            header = header_determinant(int(request_data['campaign_number']))
            create_articles_company(
                int(request_data['campaign_number']), header)
        elif 'change-button' in request.POST:
            change_data = ProcentForAd.objects.get(
                id=request_data['change-button']
            )
            change_data.koefficient = int(request_data['ad_koefficient'])
            change_data.koef_date = datetime.now()
            change_data.save()
        elif 'del-button' in request.POST:
            AdvertisingCampaign.objects.get(
                campaign_number=request_data['del-button']).delete()
        else:
            print('никуда не попала', request.POST)
        return redirect('ad_campaigns')

    context = {
        'data': company_list,
        'form': form,
        'koef_dict': koef_dict
    }
    return render(request, 'reklama/ad_campaign.html', context)
