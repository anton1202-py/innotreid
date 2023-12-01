import datetime
import json
import os
from collections import Counter
from datetime import datetime, timedelta

import pandas as pd
import requests
from celery.result import AsyncResult
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from dotenv import load_dotenv
from ozon_system.models import (AdvGroup, ArticleAmountRating, DateActionInfo,
                                GroupActions, GroupCeleryAction, GroupCompaign)
from ozon_system.tasks import start_compaign, stop_compaign

load_dotenv()

now_time = datetime.now().strftime("%Y-%m-%dT%H:%M")


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
    print(response)
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
        action_datetime__gt=datetime.now())
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
            python_datetime = datetime.strptime(
                selected_datetime, "%Y-%m-%dT%H:%M")
            adjusted_datetime = python_datetime - timedelta(hours=3)

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
            python_datetime = datetime.strptime(
                selected_datetime, "%Y-%m-%dT%H:%M")
            adjusted_datetime = python_datetime - timedelta(hours=3)

            action_object = DateActionInfo(
                company_number=compaign_id,
                action_type='start',
                action_datetime=python_datetime,
                celery_task=start_compaign.apply_async(
                    args=[compaign_id], eta=adjusted_datetime).id
            )
            action_object.save()

        elif 'del_task' in request.POST:
            print(request.POST)
            info_data = request.POST.get('del_task')
            common_data = info_data.split()
            action_id = common_data[0]
            task_id = common_data[1]
            DateActionInfo.objects.get(pk=action_id).delete()
            # AsyncResult(task_id).revoke()
        return redirect('ozon_adv_group')

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

    url_search = f"https://performance.ozon.ru:443/api/client/campaign/{campaign_id}/search_promo/products"

    if compaign_info:
        context = {
            'compaign_info': compaign_info,
            'campaign_id': campaign_id
        }
    else:
        payload = json.dumps({
            "page": 0,
            "pageSize": 1000
        })

        response_search = requests.request(
            "POST", url_search, headers=headers, data=payload)
        response_search_info = json.loads(response_search.text)['products']
        context = {
            'compaign_info': response_search_info,
            'campaign_id': campaign_id
        }

    return render(request, 'ozon_system/compaign_article_info.html', context)


def group_adv_compaign_timetable(request):
    # start_compaign(compaign)
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

    compaign_status = {}
    for compaign in compaign_data:
        compaign_status[str(compaign['id'])] = compaign['state']

    # groups - queryset с номерами всех групп.
    groups = AdvGroup.objects.all()

    # groups_info - список ID всех компаний, которые добавлены в группы.
    groups_info = GroupCompaign.objects.values_list(
        'compaign', flat=True).distinct()

    # compaigns_in_group - queryset с ID компаний в каждой группе.
    compaigns_in_group = GroupCompaign.objects.all()

    # action_with_group_datetime - queryset с действиями для групп.
    # Отфильтрован по дате выполнения, чтобы была больше текущей
    action_with_group_datetime = GroupActions.objects.all()

    # celery_actions - queryset с действиями для celery.
    celery_actions = GroupCeleryAction.objects.all()

    # Смотрю какие компании есть в ответе API и если они не добавлены в группы,
    # то есть их нет в  списке groups_info, то их добавляю в список для выбора групп
    compaigns_list = []
    for compaign in compaign_data:
        compaigns_list.append(compaign['id'])
    compaigns_list_for_select = [
        item for item in compaigns_list if item not in groups_info]

    if request.POST:
        if 'add_compaign_to_group' in request.POST.keys():
            print(request.POST)
            # Добавляет компанию в группу
            if request.POST['compaign_id']:
                compaign_id = request.POST['compaign_id']
            elif request.POST['compaign_id_input']:
                compaign_id = request.POST['compaign_id_input']
            group_number = request.POST['group_number']
            group_id = groups.get(group=group_number)
            adv_group = GroupCompaign(
                group=group_id,
                compaign=compaign_id
            )
            adv_group.save()

        elif 'del_compaign' in request.POST.keys():
            # Удаляет компанию из группы
            compaign_id = request.POST['del_compaign']
            GroupCompaign.objects.get(compaign=compaign_id).delete()
        elif 'start' in request.POST.keys():
            # Добавляет дейсвие старта рекламы в базу данных
            group_number = request.POST['start']
            selected_datetime = request.POST['start_time']
            python_datetime = datetime.strptime(
                selected_datetime, "%Y-%m-%dT%H:%M")
            group_id = groups.get(group=group_number)
            adjusted_datetime_start = python_datetime - \
                timedelta(hours=3)
            if GroupActions.objects.filter(group=group_id,
                                           action_type='start'):
                group_action_id = GroupActions.objects.get(
                    group=group_id, action_type='start')

                # Формируем список id задач Celery для удаления
                data_celery_tasks_list = GroupCeleryAction.objects.filter(
                    group_action=group_action_id
                ).values_list('celery_task', flat=True)

                # Аннулируем поставленные задачи Celery
                for task_id in data_celery_tasks_list:
                    AsyncResult(task_id).revoke()

                # Удаляем аннулированные задачи из таблицы GroupCeleryAction
                celery_tasks = GroupCeleryAction.objects.filter(
                    group_action=group_action_id
                )
                for task in celery_tasks:
                    task.delete()
                GroupActions.objects.filter(group=group_id,
                                            action_type='start').delete()

            action_start_group_for_celery = GroupActions(
                group=group_id,
                action_type='start',
                start_task_datetime=now_time,
                action_datetime=python_datetime)
            action_start_group_for_celery.save()

            # Добавляет задачу старта рекламы на каждую Компанию в Celery
            compaigns_for_celery = GroupCompaign.objects.filter(
                group=group_id).values_list(
                    'compaign', flat=True)

            for compaign in compaigns_for_celery:
                start_action_object = GroupCeleryAction(
                    group_action=action_start_group_for_celery,
                    celery_task=start_compaign.apply_async(
                        args=[compaign],
                        eta=adjusted_datetime_start).id
                )
                start_action_object.save()

        elif 'stop' in request.POST.keys():
            # Добавляет дейсвие остановки рекламы в базуу данных
            group_number = request.POST['stop']
            selected_datetime = request.POST['stop_time']
            python_datetime = datetime.strptime(
                selected_datetime, "%Y-%m-%dT%H:%M")
            group_id = groups.get(group=group_number)
            adjusted_datetime_stop = python_datetime - \
                timedelta(hours=3)
            action_stop_for_group = GroupActions(
                group=group_id,
                action_type='stop',
                start_task_datetime=now_time,
                action_datetime=python_datetime
            )
            action_stop_for_group.save()
            compaigns_for_celery = GroupCompaign.objects.filter(
                group=group_id).values_list(
                    'compaign', flat=True)
            # Добавляет задачу остановки рекламы на каждую Компанию в Celery
            for compaign in compaigns_for_celery:
                stop_action_object = GroupCeleryAction(
                    group_action=action_stop_for_group,
                    celery_task=stop_compaign.apply_async(
                        args=[compaign],
                        eta=adjusted_datetime_stop).id
                )
                stop_action_object.save()

        elif 'delete_action' in request.POST:
            # Удаляет действие из группы
            action_date_id = request.POST['action_date_id']
            group_number = request.POST['delete_action']
            group_action_id = GroupActions.objects.get(id=action_date_id)

            # Формируем список id задач Celery для удаления
            data_celery_tasks_list = GroupCeleryAction.objects.filter(
                group_action=group_action_id
            ).values_list('celery_task', flat=True)

            # Аннулируем поставленные задачи Celery
            for task_id in data_celery_tasks_list:
                AsyncResult(task_id).revoke()

            # Удаляем аннулированные задачи из таблицы GroupCeleryAction
            celery_tasks = GroupCeleryAction.objects.filter(
                group_action=group_action_id
            )
            for task in celery_tasks:
                task.delete()

            # Удаляем время действия из таблицы GroupActions
            GroupActions.objects.get(id=action_date_id).delete()

        return redirect('ozon_campaing_timetable')

    context = {
        'groups': groups,
        'compaigns_in_group': compaigns_in_group,
        'compaigns_list_for_select': compaigns_list_for_select,
        'groups_info': groups_info,
        'action_with_group_datetime': action_with_group_datetime,
        'compaign_status': compaign_status,
    }

    return render(request, 'ozon_system/group_adv_compaign_timetable.html', context)
