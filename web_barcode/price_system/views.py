import importlib
import json
import os

import requests
from django.db.models import Q
from django.shortcuts import redirect, render
from dotenv import load_dotenv

from .models import ArticleGroup, Articles, Groups

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


def wb_article_data():
    """Получаем данные всех артикулов в ВБ"""
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
    response = requests.request(
        "POST", url, headers=wb_headers_karavaev, data=payload)
    all_data = json.loads(response.text)["cards"]
    return all_data


def wb_article_compare():
    """Достаем данные всех артиуклов ВБ, необходимые для сверки"""
    all_data = wb_article_data()
    article_dict = {}
    for data in all_data:
        if data["subjectName"] == "Ночники":
            article = data["vendorCode"].split('-')[0]
            article_dict[article.capitalize()] = [data["vendorCode"],
                                                  data["sizes"][0]["skus"][0], data["nmID"]]
    sorted_article_dict = dict(sorted(article_dict.items()))
    return sorted_article_dict


def ozon_raw_articles():

    url = "https://api-seller.ozon.ru/v2/product/list"

    payload = json.dumps({
        "last_id": "",
        "limit": 1000
    })

    response = requests.request(
        "POST", url, headers=ozon_headers_karavaev, data=payload)
    ozon_data = json.loads(response.text)["result"]["items"]

    raw_article_ozon_list = []
    for dat in ozon_data:
        raw_article_ozon_list.append(dat["product_id"])
    # print(raw_article_ozon_list)
    return raw_article_ozon_list


def ozon_cleaning_articles():
    urls = 'https://api-seller.ozon.ru/v2/product/info/list'
    raw_article_ozon_list = ozon_raw_articles()

    payload = json.dumps({
        "offer_id": [],
        "product_id": raw_article_ozon_list,
        "sku": []
    })
    article_ozon_dict = {}
    response = requests.request(
        "POST", urls, headers=ozon_headers_karavaev, data=payload)
    ozon_data = json.loads(response.text)["result"]["items"]
    for dat in ozon_data:
        if 'Ночник' in dat["name"]:
            article = dat["offer_id"].split('-')[0]
            article_ozon_dict[article] = [
                dat["offer_id"], int(dat["barcode"]), dat["id"], dat["id"], dat["sku"], dat["fbo_sku"], dat["fbs_sku"]]
    return article_ozon_dict


def yandex_raw_articles_data(nextPageToken='', raw_articles_list=None):
    """Создает и возвращает словарь с данными fbs_sku_data {артикул: остаток_fbs}"""

    if raw_articles_list == None:
        raw_articles_list = []
    url = f'https://api.partner.market.yandex.ru/businesses/3345369/offer-mappings?limit=200&page_token={nextPageToken}'
    payload = json.dumps({})

    response = requests.request(
        "POST", url, headers=yandex_headers_karavaev, data=payload)
    main_articles_data = json.loads(response.text)['result']
    articles_data = main_articles_data['offerMappings']
    for article in articles_data:

        if 'Ночник' in article['offer']['name']:
            inner_list = []
            # print(article['offer'].keys())
            if article['offer']['barcodes']:
                # print(article['offer']['offerId'])
                inner_list.append(article['offer']['offerId'])
                inner_list.append(article['offer']['barcodes'][0])
                inner_list.append(article['mapping']['marketSku'])
                raw_articles_list.append(inner_list)
    if main_articles_data['paging']:
        yandex_raw_articles_data(
            main_articles_data['paging']['nextPageToken'], raw_articles_list)
    return raw_articles_list


def yandex_articles():
    """Формирует данные для сопоставления"""
    raw_articles_list = yandex_raw_articles_data()
    article_yandex_dict = {}
    for article in raw_articles_list:
        common_article = article[0].split('-')[0]
        article_yandex_dict[common_article] = article
    return article_yandex_dict


def wb_matching_articles():
    """Функция сопоставляет артикулы с WB с общей базой"""
    wb_article_data = wb_article_compare()
    for common_article, wb_data in wb_article_data.items():
        if Articles.objects.filter(common_article=common_article).exists() == True:
            wb_article = Articles.objects.get(
                common_article=common_article)
            if wb_article.wb_seller_article != wb_data[0] or str(wb_article.wb_barcode) != str(wb_data[1]) or wb_article.wb_nomenclature != wb_data[2]:
                wb_article.status = 'Не сопоставлено'
                wb_article.save()
                print(
                    f'проверьте артикул {common_article} на вб вручную. Не совпали данные')
            else:
                wb_article.status = 'Сопоставлено'
                wb_article.save()
        else:
            wb = Articles(
                common_article=common_article,
                status='Сопоставлено',
                wb_seller_article=wb_data[0],
                wb_barcode=wb_data[1],
                wb_nomenclature=wb_data[2]
            )
            wb.save()


def ozon_matching_articles():
    """Функция сопоставляет артикулы с Ozon с общей базой"""
    ozon_article_data = ozon_cleaning_articles()
    for common_article, ozon_data in ozon_article_data.items():
        if Articles.objects.filter(common_article=common_article).exists() == True:
            ozon_article = Articles.objects.get(
                common_article=common_article)
            if (ozon_article.ozon_seller_article != ozon_data[0] and ozon_article.ozon_seller_article != None
                or str(ozon_article.ozon_barcode) != str(ozon_data[1]) and ozon_article.ozon_barcode != None
                or ozon_article.ozon_product_id != ozon_data[2] and ozon_article.ozon_product_id != None
                or ozon_article.ozon_sku != ozon_data[3] and ozon_article.ozon_sku != None
                or ozon_article.ozon_fbo_sku_id != ozon_data[4] and ozon_article.ozon_fbo_sku_id != None
                    or ozon_article.ozon_fbs_sku_id != ozon_data[5] and ozon_article.ozon_fbs_sku_id != None):
                ozon_article.status = 'Не сопоставлено'
                ozon_article.save()
                print(
                    f'проверьте артикул {common_article} на ozon вручную. Не совпали данные')
            elif ozon_article.ozon_barcode == None:
                print('alarm**************', type(ozon_data[1]))
                ozon = Articles.objects.get(common_article=common_article)
                ozon.status = 'Сопоставлено'
                ozon.ozon_seller_article = ozon_data[0]
                ozon.ozon_barcode = ozon_data[1]
                ozon.ozon_product_id = int(ozon_data[2])
                ozon.ozon_sku = int(ozon_data[3])
                ozon.ozon_fbo_sku_id = int(ozon_data[4])
                ozon.ozon_fbs_sku_id = int(ozon_data[5])
                ozon.save()
            else:
                ozon_article.status = 'Сопоставлено'
                ozon_article.save()
        else:
            ozon = Articles(
                common_article=common_article,
                status='Сопоставлено',
                ozon_seller_article=ozon_data[0],
                ozon_barcode=int(ozon_data[1]),
                ozon_product_id=int(ozon_data[2]),
                ozon_sku=int(ozon_data[3]),
                ozon_fbo_sku_id=int(ozon_data[4]),
                ozon_fbs_sku_id=int(ozon_data[5])
            )
            ozon.save()


def yandex_matching_articles():
    """Функция сопоставляет артикулы с Яндекса с общей базой"""
    yandex_article_data = yandex_articles()
    for common_article, yandex_data in yandex_article_data.items():
        if Articles.objects.filter(common_article=common_article).exists() == True:
            yandex_article = Articles.objects.get(
                common_article=common_article)
            if (yandex_article.yandex_seller_article != yandex_data[0] and yandex_article.yandex_seller_article != None
                or str(yandex_article.yandex_barcode) != str(yandex_data[1]) and yandex_article.yandex_barcode != None
                    or yandex_article.yandex_sku != yandex_data[2] and yandex_article.yandex_sku != None):
                yandex_article.status = 'Не сопоставлено'
                yandex_article.save()
                print(
                    f'проверьте артикул {common_article} на ozon вручную. Не совпали данные')
            elif yandex_article.yandex_barcode == None:
                yandex = Articles.objects.get(common_article=common_article)
                yandex.status = 'Сопоставлено'
                yandex.yandex_seller_article = yandex_data[0]
                yandex.yandex_barcode = yandex_data[1]
                yandex.yandex_sku = int(yandex_data[2])

                yandex.save()
            else:
                yandex_article.status = 'Сопоставлено'
                yandex_article.save()
        else:
            yandex = Articles(
                common_article=common_article,
                status='Сопоставлено',
                yandex_seller_article=yandex_data[0],
                yandex_barcode=int(yandex_data[1]),
                yandex_sku=int(yandex_data[2])
            )
            yandex.save()


def article_compare(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    data = Articles.objects.all().order_by("common_article")

    if request.method == 'POST':
        wb_matching_articles()
        ozon_matching_articles()
        yandex_matching_articles()
    context = {
        'data': data,
    }
    return render(request, 'price_system/article_compare.html', context)


def groups_view(request):
    """Отвечает за представление страницы с добавлением артикула в БД"""
    data = Groups.objects.all().order_by('name')
    context = {
        'data': data,
    }
    if request.method == 'POST' and 'add_button' in request.POST.keys():
        request_data = request.POST
        print(request_data)
        if Groups.objects.filter(Q(name=request_data['name'])).exists():
            Groups.objects.filter(name=request_data['name']).update(
                name=request_data['name'],
                wb_price=request_data['wb_price'],
                ozon_price=request_data['ozon_price'],
                yandex_price=request_data['yandex_price']
            )
        else:
            obj, created = Groups.objects.get_or_create(
                name=request_data['name'],
                wb_price=request_data['wb_price'],
                ozon_price=request_data['ozon_price'],
                yandex_price=request_data['yandex_price']
            )
        return redirect('price_groups')
    elif request.method == 'POST' and 'change_button' in request.POST.keys():
        request_data = request.POST
        Groups.objects.filter(id=request_data['change_button']).update(
            name=request_data['name'],
        )
        return redirect('price_groups')
    elif request.method == 'POST' and 'del-button' in request.POST.keys():
        print(request.POST)
        Groups.objects.get(
            name=request.POST['del-button']).delete()
        return redirect('price_groups')
    return render(request, 'price_system/groups.html', context)
