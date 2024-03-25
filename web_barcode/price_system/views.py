from datetime import datetime, timedelta

from django.db.models import Q
from django.shortcuts import redirect, render
from django.views.generic import ListView

from .forms import FilterChooseGroupForm
from .models import ArticleGroup, Articles, ArticlesPrice, Groups
from .periodical_tasks import (ozon_add_price_info, wb_add_price_info,
                               yandex_add_price_info)
from .supplyment import (excel_compare_table, excel_creating_mod,
                         excel_import_data, ozon_cleaning_articles,
                         ozon_matching_articles, ozon_price_change,
                         ozon_raw_articles, super_test, wb_matching_articles,
                         wilberries_price_change, yandex_articles,
                         yandex_matching_articles, yandex_price_change,
                         yandex_raw_articles_data)


def ip_article_compare(request):
    """Отображает страницу с таблицей сопоставления ИП"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    data = Articles.objects.filter(
        company='ИП Караваев').order_by("common_article")
    # super_test()
    if request.POST:
        if "compare" in request.POST:
            wb_matching_articles('ИП Караваев')
            # ozon_matching_articles()
            # yandex_matching_articles()

        elif 'excel_export' in request.POST:
            return excel_compare_table(data)

        elif 'filter' in request.POST:
            filter_data = request.POST
            article_filter = filter_data.get("common_article")
            status_filter = filter_data.get("status")

            if article_filter:
                data = data.filter(
                    Q(common_article=article_filter)).order_by('id')
            if status_filter:
                data = data.filter(
                    Q(status=status_filter)).order_by('id')

    context = {
        'data': data,
    }
    return render(request, 'price_system/article_compare.html', context)


def ooo_article_compare(request):
    """Отображает страницу с таблицей сопоставления ООО"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    data = Articles.objects.filter(
        company='ООО Иннотрейд').order_by("common_article")
    # super_test()
    if request.POST:
        if "compare" in request.POST:
            # wb_matching_articles('ООО Иннотрейд')
            # ozon_matching_articles('ООО Иннотрейд')
            yandex_matching_articles('ООО Иннотрейд')
        elif 'excel_export' in request.POST:
            return excel_compare_table(data)
        elif 'filter' in request.POST:
            filter_data = request.POST
            article_filter = filter_data.get("common_article")
            status_filter = filter_data.get("status")
            print(status_filter)
            if article_filter:
                data = data.filter(
                    Q(common_article=article_filter)).order_by('id')
            if status_filter:
                data = data.filter(
                    Q(status=status_filter)).order_by('id')
                print(data)
    context = {
        'data': data,
    }
    return render(request, 'price_system/ooo_article_compare.html', context)


def ip_groups_view(request):
    """Отвечает за Отображение ценовых групп"""
    data = Groups.objects.all().order_by('name')
    context = {
        'data': data,
    }
    if request.POST:
        if 'add_button' in request.POST.keys():
            request_data = request.POST
            obj, created = Groups.objects.get_or_create(
                name=request_data['name'],
                wb_price=request_data['wb_price'],
                wb_discount=request_data['wb_discount'],
                ozon_price=request_data['ozon_price'],
                yandex_price=request_data['yandex_price'],
                min_price=request_data['min_price'],
                old_price=request_data['old_price']
            )
        elif 'change_button' in request.POST.keys():
            request_data = request.POST
            Groups.objects.filter(id=request_data['change_button']).update(
                name=request_data['name'],
                wb_price=request_data['wb_price'],
                wb_discount=request_data['wb_discount'],
                ozon_price=request_data['ozon_price'],
                yandex_price=request_data['yandex_price'],
                min_price=request_data['min_price'],
                old_price=request_data['old_price']
            )
        elif 'del-button' in request.POST.keys():
            Groups.objects.get(
                name=request.POST['del-button']).delete()
        elif 'action_price' in request.POST:
            names = ArticleGroup.objects.filter(
                group=request.POST['action_price'])
            wb_price = names[0].group.wb_price
            wb_discount = names[0].group.wb_discount
            ozon_price = names[0].group.ozon_price
            yandex_price = names[0].group.yandex_price
            min_price = names[0].group.min_price
            old_price = names[0].group.old_price
            wb_nom_list = []
            oz_nom_list = []
            yandex_nom_list = []
            for art in names:
                wb_nom_list.append(art.common_article.wb_nomenclature)
                oz_nom_list.append(art.common_article.ozon_product_id)
                yandex_nom_list.append(
                    art.common_article.yandex_seller_article)

            wilberries_price_change(wb_nom_list, wb_price, wb_discount)
            ozon_price_change(oz_nom_list, ozon_price, min_price, old_price)
            yandex_price_change(yandex_nom_list, yandex_price, old_price)

            # Записываем изененные цены в базу данных
            wb_add_price_info()
            ozon_add_price_info()
            yandex_add_price_info()
        return redirect('price_groups_ip')
    return render(request, 'price_system/groups.html', context)


def ip_article_groups_view(request):
    """Отвечает за сопоставление артикула и группы"""
    articles_data = Articles.objects.all().values('pk')
    filter_data = Groups.objects.all().values('name')
    form = FilterChooseGroupForm(request.POST)
    for article_id in articles_data:
        if not ArticleGroup.objects.filter(common_article=article_id['pk']).exists():
            obj = ArticleGroup(
                common_article=Articles.objects.get(id=article_id['pk']))
            obj.save()
    data = ArticleGroup.objects.all().order_by('common_article')
    if request.POST:
        if request.POST.get('export') == 'create_file':
            return excel_creating_mod(data)
        elif 'import_file' in request.FILES:
            excel_import_data(request.FILES['import_file'])
        elif 'filter' in request.POST:
            filter_data = request.POST
            article_filter = filter_data.get("common_article")
            group_filter = filter_data.get("group_name")

            if article_filter:
                if Articles.objects.filter(common_article=article_filter).exists():
                    data = data.filter(
                        Q(common_article=Articles.objects.filter(common_article=article_filter)[0])).order_by('id')
                else:
                    data = data.filter(
                        Q(common_article=0)).order_by('id')
            if group_filter:
                data = data.filter(
                    Q(group=Groups.objects.filter(id=group_filter)[0])).order_by('id')
        elif 'group_name' in request.POST:
            if request.POST['change_group']:
                print('Не пустая')
                ArticleGroup.objects.filter(id=request.POST['group_name']).update(
                    group=Groups.objects.get(name=request.POST['change_group'])
                )
            elif len(request.POST['change_group']) == 0:
                article = ArticleGroup.objects.get(
                    id=request.POST['group_name'])
                article.group = None
                article.save()

    context = {
        'data': data,
        'form': form,
        'filter_data': filter_data,
    }
    return render(request, 'price_system/article_groups.html', context)


def ip_article_price_statistic(request):
    """Отображает статистику по изменениею цен артикулов"""

    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)
    data = ArticlesPrice.objects.filter(
        price_date__gte=start_date).order_by('common_article')
    price_date = ArticlesPrice.objects.filter(
        price_date__gte=start_date).values('price_date').distinct()
    article_list = Articles.objects.all().order_by('common_article')
    date_list = []
    for i in price_date:
        date_list.append(i['price_date'])
    date_list.sort(reverse=True)
    data_for_user = {}
    for article in article_list:
        inner_dict = {}
        for date in date_list:
            mp_dict = {}
            article_data = data.filter(
                price_date=date,
                common_article=Articles.objects.get(common_article=article))
            for i in article_data:
                if i.marketplace == 'Wildberries':
                    mp_dict['wb_price'] = i.price
                if i.marketplace == 'Ozon':
                    mp_dict['ozon_price'] = i.price
                if i.marketplace == 'Yandex':
                    mp_dict['yandex_price'] = i.price
            inner_dict[str(date)] = mp_dict
            data_for_user[article.common_article] = inner_dict

    context = {
        'data': data,
        'date_list': date_list,
        'article_list': article_list,
        'data_for_user': data_for_user,
    }
    return render(request, 'price_system/article_price_statistic.html', context)


class IpArticleCompareDetailView(ListView):
    model = Articles
    template_name = 'price_system/article_compare_detail.html'
    context_object_name = 'data'

    def get_context_data(self, **kwargs):
        context = super(IpArticleCompareDetailView,
                        self).get_context_data(**kwargs)
        return context

    def post(self, request, *args, **kwargs):
        if request.POST:
            post_data = request.POST
            article = Articles.objects.get(
                common_article=self.kwargs['common_article'])
            article.status = 'Сопоставлено'
            article.wb_seller_article = post_data.get('wb_seller_article')
            article.wb_barcode = post_data.get('wb_barcode')
            article.wb_nomenclature = post_data.get('wb_nomenclature')

            article.ozon_seller_article = post_data.get('ozon_seller_article')
            article.ozon_barcode = post_data.get('ozon_barcode')
            article.ozon_product_id = post_data.get('ozon_product_id')
            article.ozon_sku = post_data.get('ozon_sku')
            article.ozon_fbo_sku_id = post_data.get('ozon_fbo_sku_id')
            article.ozon_fbs_sku_id = post_data.get('ozon_fbs_sku_id')

            article.yandex_seller_article = post_data.get(
                'yandex_seller_article')
            article.yandex_barcode = post_data.get('yandex_barcode')
            article.yandex_sku = post_data.get('yandex_sku')
            article.save()
        return redirect('article_compare_detail_ip', self.kwargs['common_article'])

    def get_queryset(self):
        return Articles.objects.filter(
            common_article=self.kwargs['common_article'])
