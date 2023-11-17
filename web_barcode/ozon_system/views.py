import datetime
import json
import os
from collections import Counter

import pandas as pd
import requests
from celery.result import AsyncResult
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from dotenv import load_dotenv
from ozon_system.models import ArticleAmountRating, DateActionInfo
from ozon_system.tasks import start_compaign, stop_compaign

load_dotenv()


def access_token():
    url = "https://performance.ozon.ru/api/client/token"

    payload = json.dumps({
        "client_id": os.getenv('CLIENT_ACCESS_ID'),
        "client_secret": os.getenv('CLIENT_SECRET'),
        "grant_type": "client_credentials"
    })
    headers = {
        'Content-Type': 'application/json',
        'Headers': os.getenv('OZON_API_TOKEN'),
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return json.loads(response.text)['access_token']


def ozon_main_info_table(request):
    articles_sale_data_for_table = {}
    main_data = ArticleAmountRating.objects.all()

    if request.method == 'POST' and 'show_statistic' in request.POST.keys():
        payload = json.dumps({
            "filter": {
                "date": {
                    "from": f"{request.POST['datestart']}T00:00:00.000Z",
                    "to": f"{request.POST['datefinish']}T00:00:00.000Z",
                },
                "operation_type": ['OperationAgentDeliveredToCustomer'],
                "posting_number": "",
                "transaction_type": "all"
            },
            "page": 1,
            "page_size": 1000
        })
        headers = {
            'Client-Id': os.getenv('CLIENT_ID'),
            'Api-Key': os.getenv('OZON_API_TOKEN'),
            'Content-Type': 'application/json',
        }
        SALE_ARTICLE_URL = "https://api-seller.ozon.ru/v3/finance/transaction/list"
        response = requests.request(
            "POST", SALE_ARTICLE_URL, headers=headers, data=payload)
        common_ozon_sale_data = json.loads(response.text)
        # print('common_ozon_sale_data', common_ozon_sale_data)
        article_list = []
        sale_data = common_ozon_sale_data['result']['operations']
        for i in sale_data:
            if i['operation_type'] == 'OperationAgentDeliveredToCustomer':
                article_list.append(i['items'][0]['name'])

        raw_article_dict = Counter(article_list)
        raw_articles_sale_data_for_table = {}

        for key, value in raw_article_dict.items():
            amount_price = 0
            sku = ''
            for article in sale_data:
                if article['operation_type'] == 'OperationAgentDeliveredToCustomer':
                    if key == article['items'][0]['name']:
                        amount_price += article['accruals_for_sale']
                        sku = article['items'][0]['sku']
            raw_articles_sale_data_for_table[key] = [value, amount_price, sku]

        articles_sale_data_for_table = dict(
            sorted(raw_articles_sale_data_for_table.items(), key=lambda x: x[1][0], reverse=True))

    if request.method == 'POST' and 'add_article_group' in request.POST.keys():
        print(request.POST)
        main_data = ArticleAmountRating.objects.all()
        for data in main_data:
            if data.pk % 3 == 1:
                data.article_group = 1
            elif data.pk % 3 == 2:
                data.article_group = 2
            elif data.pk % 3 == 0:
                data.article_group = 3
            data.save()

    context = {
        'main_data': main_data,
        'table_data': articles_sale_data_for_table
    }
    return render(request, 'ozon_system/main_table.html', context)


def ozon_adv_group(request):
    action_with_company_datetime = DateActionInfo.objects.filter(
        action_datetime__gt=datetime.datetime.now())
    print(action_with_company_datetime)
    url = "https://performance.ozon.ru/api/client/campaign?state=CAMPAIGN_STATE_UNKNOWN"

    payload = json.dumps({
        "filter": {
            "operation_type": [],
            "posting_number": "",
            "transaction_type": "all"
        },
        "page": 1,
        "page_size": 1000
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token()}',
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    compaign_data = json.loads(response.text)['list']

    if request.POST:

        if 'stop' in request.POST.keys():

            compaign_id = request.POST['stop']
            selected_datetime = request.POST['stop_time']
            python_datetime = datetime.datetime.strptime(
                selected_datetime, "%Y-%m-%dT%H:%M")
            adjusted_datetime = python_datetime - datetime.timedelta(hours=3)

            # stop_compaign.apply_async(
            #     args=[compaign_id], eta=adjusted_datetime)

            # if DateActionInfo.objects.filter(Q(company_number=compaign_id) & Q(action_type='stop') & Q(action_datetime=python_datetime)):
            #     DateActionInfo.objects.filter(Q(company_number=compaign_id) & Q(action_type='stop') & Q(action_datetime=python_datetime)).update(
            #         start_task_datetime=datetime.datetime.now(),
            #     )
            # else:
            # stop_compaign.apply_async(
            #     args=[compaign_id], eta=adjusted_datetime)
            action_object = DateActionInfo(
                company_number=compaign_id,
                action_type='stop',
                action_datetime=python_datetime,
                celery_task=stop_compaign.apply_async(
                    args=[compaign_id], eta=adjusted_datetime).id
            )
            action_object.save()

        elif 'start' in request.POST.keys():
            compaign_id = request.POST['start']
            selected_datetime = request.POST['start_time']
            python_datetime = datetime.datetime.strptime(
                selected_datetime, "%Y-%m-%dT%H:%M")
            adjusted_datetime = python_datetime - datetime.timedelta(hours=3)
            print('Перед функцией')
            # celery_task_start = start_compaign.apply_async(
            #    args=[compaign_id], eta=adjusted_datetime)
            print('Прошел функцию')

            if DateActionInfo.objects.filter(Q(company_number=compaign_id) & Q(action_type='start') & Q(action_datetime=python_datetime)):
                DateActionInfo.objects.filter(Q(company_number=compaign_id) & Q(action_type='start') & Q(action_datetime=python_datetime)).update(
                    start_task_datetime=datetime.datetime.now(),
                )
            else:
                start_compaign.apply_async(
                    args=[compaign_id], eta=adjusted_datetime)
                action_object = DateActionInfo(
                    company_number=compaign_id,
                    action_type='start',
                    action_datetime=python_datetime,
                    celery_task=start_compaign.apply_async(
                        args=[compaign_id], eta=adjusted_datetime).id
                )
                action_object.save()
        elif 'del_task' in request.POST:
            info_data = request.POST.get('del_task')
            common_data = info_data.split()
            action_id = common_data[0]
            task_id = common_data[1]
            DateActionInfo.objects.get(pk=action_id).delete()
            AsyncResult(task_id).revoke()

    context = {
        'action_data': action_with_company_datetime,
        'compaign_data': compaign_data,
    }
    return render(request, 'ozon_system/compaign_data.html', context)


def ozon_campaing_article_info(request, campaign_id):
    url = f"https://performance.ozon.ru:443/api/client/campaign/{campaign_id}/products"

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token()}',
    }

    response = requests.request("GET", url, headers=headers)

    compaign_info = json.loads(response.text)['products']
    context = {
        'compaign_info': compaign_info,
        'campaign_id': campaign_id
    }

    return render(request, 'ozon_system/compaign_article_info.html', context)
