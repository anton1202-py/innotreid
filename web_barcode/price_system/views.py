import importlib
import json
import os
from django.shortcuts import redirect, render

import requests

from .models import Articles

articles = Articles.objects.all().values_list('common_article')

def wb_article_compare():
    url = "https://suppliers-api.wildberries.ru/content/v2/get/cards/list"
    payload = json.dumps({
        "settings": {
            "cursor": {
                "limit": 1000
            },
            "filter": {
                "withPhoto": -1
            }
        }
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjMxMDI1djEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTcxNzgwNTUzNywiaWQiOiI1ZGVlMDU0Ni03NzVkLTRjNDUtYmQyZC0wYzUwYTZjN2VkMmMiLCJpaWQiOjY1NzgwMzAxLCJvaWQiOjQ4NDkxNSwicyI6NTEwLCJzaWQiOiI4NTE3NTJjYi0xZDY1LTRhYmEtYWZjNC03NDJhMjVlMTAwYzkiLCJ1aWQiOjY1NzgwMzAxfQ.IY9GEI-AghSxGt6JYyjTVULI83UuzGGuL6Q3NZhWSa1ks7quDwXdhWePRcGr7RoMZCAZP9oduWJ9h5U-q2fd-w'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    article_dict = {}
    all_data = json.loads(response.text)["cards"]
    for data in all_data:
        if data["subjectName"] == "Ночники":
            article = data["vendorCode"].split('-')[0]
            #article = data["vendorCode"]
            article_dict[article.capitalize()] = data["vendorCode"]
        # print(data["vendorCode"])
    # sorted_list = sorted(article_list)
    # print(sorted_list)
    sorted_article_dict = dict(sorted(article_dict.items()))
    return sorted_article_dict


def ozon_raw_articles():

    url = "https://api-seller.ozon.ru/v2/product/list"

    payload = json.dumps({
        "last_id": "",
        "limit": 1000
    })
    headers = {
        'Client-Id': '282094',
        'Api-Key': '27bd60c7-00b0-4598-ba54-ab501513734e',
        'Content-Type': 'application/json',
        'Cookie': 'abt_data=248d06066a90f9d41616b68cd971eea9:83ce6c51b2873456ca7c9ea3873e75483542035bc44882e97c1838536ed37e8c972db7aa69a111d01c253df2dc80750d9eae1133efd45ca44f4ccfda9cd283f77ffd7991d45b80b19232832359e29d6941a0cc3b31460f01e5ffbdacf6bed574e2e31e827de37aa8be87162ef6c206eb8d022771b24ee536d9497a71e26aec54d8e8d27c826ec8878dd418b7bc3ed7e5efbe2d59a13f9b139c348ea601520a1a; __cf_bm=nRa8cb6NTbL_DQw4ahY2rl7iRAPK1v91qWJm30Rv2Qk-1707920614-1.0-AY3MqUURVtHnqylYy1Vox3xEzjmSxk5QUkWR9dp2kZAMhd54k4h3uHpVEqGvKIYc0B/Z1uaQwkD2sex67/jUfZk='
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    ozon_data = json.loads(response.text)["result"]["items"]

    raw_article_ozon_list = []
    for dat in ozon_data:
        raw_article_ozon_list.append(dat["offer_id"])

    return raw_article_ozon_list


def ozon_cleaning_articles():
    urls = 'https://api-seller.ozon.ru/v2/product/info/list'
    raw_article_ozon_list = ozon_raw_articles()

    payload = json.dumps({
        "offer_id": raw_article_ozon_list,
        "product_id": [],
        "sku": []
    })
    headers = {
        'Client-Id': '282094',
        'Api-Key': '27bd60c7-00b0-4598-ba54-ab501513734e',
        'Content-Type': 'application/json',
        'Cookie': 'abt_data=248d06066a90f9d41616b68cd971eea9:83ce6c51b2873456ca7c9ea3873e75483542035bc44882e97c1838536ed37e8c972db7aa69a111d01c253df2dc80750d9eae1133efd45ca44f4ccfda9cd283f77ffd7991d45b80b19232832359e29d6941a0cc3b31460f01e5ffbdacf6bed574e2e31e827de37aa8be87162ef6c206eb8d022771b24ee536d9497a71e26aec54d8e8d27c826ec8878dd418b7bc3ed7e5efbe2d59a13f9b139c348ea601520a1a; __cf_bm=nRa8cb6NTbL_DQw4ahY2rl7iRAPK1v91qWJm30Rv2Qk-1707920614-1.0-AY3MqUURVtHnqylYy1Vox3xEzjmSxk5QUkWR9dp2kZAMhd54k4h3uHpVEqGvKIYc0B/Z1uaQwkD2sex67/jUfZk='
    }
    article_ozon_dict = {}
    response = requests.request("POST", urls, headers=headers, data=payload)
    ozon_data = json.loads(response.text)["result"]["items"]
    for dat in ozon_data:
        if 'Ночник' in dat["name"]:
            article = dat["offer_id"].split('-')[0]
            article_ozon_dict[article] = dat["offer_id"]
    return article_ozon_dict

def database_home(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    # if request.user.is_staff == True:
    wb_article_data = wb_article_compare()
    ozon_data = 
    data = Articles.objects.all()
    context = {
        'data': data,
    }
    if request.method == 'POST':

    return render(request, 'database/database_home.html', context)






def yandex_raw_articles_data(nextPageToken='', raw_articles_list=None):
    """Создает и возвращает словарь с данными fbs_sku_data {артикул: остаток_fbs}"""

    if raw_articles_list == None:
        raw_articles_list = []
    url = f'https://api.partner.market.yandex.ru/businesses/3345369/offer-mappings?limit=200&page_token={nextPageToken}'
    payload = json.dumps({})
    headers = {
        'Authorization': 'Bearer y0_AgAEA7qjt7KxAAsqvwAAAAD41FbqtbLtPHKuSHe9_Q5iz130Eo1Ir9s',
        'Cookie': '_yasc=PVZzFPGthzxlBhvs7JA8idi5lDzgWZM5Tzm8VVzj8iGV3tc4nX35mfkgMaNdqE1gUu4=; i=taeeJze90AT1AWruvCjlwy5bT+Vrl9GJGmXAonQTIVL6H9bohd38CHzQOHsneNihABKN+WiduMPJPM1bsf1WFaoYFPA=; yandexuid=9102588391705520143'
    }
    response = requests.request(
        "POST", url, headers=headers, data=payload)
    main_articles_data = json.loads(response.text)['result']
    articles_data = main_articles_data['offerMappings']
    for article in articles_data:
        # print(article['offer']['offerId'])
        if article['offer']['vendor'] == '3Д-НОЧНИК':
            raw_articles_list.append(article['offer']['offerId'])
    if main_articles_data['paging']:
        yandex_raw_articles_data(
            main_articles_data['paging']['nextPageToken'], raw_articles_list)
    return raw_articles_list


def yandex_articles():
    raw_articles_list = yandex_raw_articles_data()

    cleaning_yandex_list = []
    for article in raw_articles_list:
        # art = article.split('-')[0]
        art = article
        cleaning_yandex_list.append(art)
        if art not in article_list:
            print(art)


yandex_articles()


# ozon_cleaning_articles()

