import asyncio
from datetime import datetime, timedelta

from asgiref.sync import sync_to_async
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.views.generic import ListView
from ozon_system.supplyment import \
    delete_ozon_articles_with_low_price_current_ur_lico
from price_system.spp_mode import article_spp_info

from .forms import FilterChooseGroupForm
from .models import ArticleGroup, Articles, ArticlesPrice, Groups
from .periodical_tasks import (ozon_add_price_info, wb_add_price_info,
                               write_group_spp_data, yandex_add_price_info)
from .supplyment import (excel_article_costprice_export, excel_compare_table,
                         excel_creating_mod,
                         excel_import_article_costprice_data,
                         excel_import_data, excel_import_group_create_data,
                         excel_with_price_groups_creating_mod,
                         ozon_articles_list, ozon_matching_articles,
                         ozon_price_change, wb_articles_list,
                         wb_matching_articles, wilberries_price_change,
                         yandex_matching_articles, yandex_price_change)


def article_compare(request, ur_lico: str):
    """Отображает страницу с таблицей сопоставления ООО"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = f'Таблица сопоставления артикулов {ur_lico}'
    data = Articles.objects.filter(
        company=ur_lico).order_by("common_article")
    if request.POST:
        if "compare" in request.POST:
            wb_matching_articles(ur_lico)
            ozon_matching_articles(ur_lico)
            yandex_matching_articles(ur_lico)
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
        elif 'export_costprice' in request.POST:
            return excel_article_costprice_export(data)
        elif 'import_file_costprice' in request.FILES:
            excel_import_article_costprice_data(
                request.FILES['import_file_costprice'], ur_lico)
    context = {
        'data': data,
        'page_name': page_name,
    }
    return render(request, 'price_system/article_compare.html', context)


def ooo_article_compare(request):
    """Отвечает за представление страницы сопоставления ООО"""
    return article_compare(request, 'ООО Иннотрейд')


def ip_article_compare(request):
    """Отвечает за представление страницы сопоставления ИП"""
    return article_compare(request, 'ИП Караваев')


def gramoty_article_compare(request):
    """Отвечает за представление страницы сопоставления ООО Мастерская чудес"""
    return article_compare(request, 'ООО Мастерская чудес')


def groups_view(request, ur_lico):
    """Отвечает за Отображение ценовых групп"""
    data = Groups.objects.filter(company=ur_lico).order_by('id')
    page_name = f'Ценовые группы {ur_lico}'
    import_data_error_text = ''

    if request.POST:
        if request.POST.get('export') == 'create_file':
            return excel_with_price_groups_creating_mod(data, ur_lico)
        elif 'import_file' in request.FILES:
            import_data_error_text = excel_import_group_create_data(
                request.FILES['import_file'], ur_lico)
        elif 'add_button' in request.POST.keys():
            request_data = request.POST
            obj, created = Groups.objects.get_or_create(
                name=request_data['name'],
                company=ur_lico,
                wb_price=request_data['old_price'],
                wb_discount=request_data['wb_discount'],
                ozon_price=request_data['ozon_price'],
                yandex_price=request_data['yandex_price'],
                min_price=request_data['min_price'],
                old_price=request_data['old_price']
            )
        elif 'change_button' in request.POST.keys():
            request_data = request.POST
            data.filter(id=request_data['change_button']).update(
                name=request_data['name'],
                wb_price=request_data['old_price'],
                wb_discount=request_data['wb_discount'],
                ozon_price=request_data['ozon_price'],
                yandex_price=request_data['yandex_price'],
                min_price=request_data['min_price'],
                old_price=request_data['old_price']
            )
        elif 'del-button' in request.POST.keys():
            data.filter(company=ur_lico,
                        name=request.POST['del-button'])[0].delete()
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
            wilberries_price_change(
                ur_lico, wb_nom_list, wb_price, wb_discount)
            ozon_price_change(ur_lico, oz_nom_list,
                              ozon_price, min_price, old_price)
            yandex_price_change(ur_lico, yandex_nom_list,
                                yandex_price, old_price)
            # Записываем изененные цены в базу данных
            wb_add_price_info(ur_lico)
            ozon_add_price_info(ur_lico)
            yandex_add_price_info(ur_lico)
        elif 'all_groups_approval' in request.POST:
            groups_name = Groups.objects.filter(
                company=ur_lico
            )
            for group in groups_name:
                names = ArticleGroup.objects.filter(
                    group=group)
                if names:
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
                    wilberries_price_change(
                        ur_lico, wb_nom_list, wb_price, wb_discount)
                    ozon_price_change(ur_lico, oz_nom_list,
                                      ozon_price, min_price, old_price)
                    yandex_price_change(ur_lico, yandex_nom_list,
                                        yandex_price, old_price)
        if 'delete_low_price_button' in request.POST:
            # Удаляем артикулы из акции, если цена в акции ниже,
            # чем установленная минимальная цена.
            delete_ozon_articles_with_low_price_current_ur_lico(ur_lico)

    context = {
        'data': data,
        'ur_lico': ur_lico,
        'page_name': page_name,
        'import_data_error_text': import_data_error_text,
    }
    return render(request, 'price_system/groups.html', context)


def ip_groups_view(request):
    """Отвечает за Отображение ценовых групп ИП"""
    return groups_view(request, 'ИП Караваев')


def ooo_groups_view(request):
    """Отвечает за Отображение ценовых групп ООО"""
    return groups_view(request, 'ООО Иннотрейд')


def gramoty_groups_view(request):
    """Отвечает за Отображение ценовых групп ООО Мастерская чудес"""
    return groups_view(request, 'ООО Мастерская чудес')


def article_groups_view(request, ur_lico):
    """Описывает общее представление сопоставление артикула и группы"""
    articles_data = Articles.objects.filter(company=ur_lico).values('pk')
    page_name = f'Таблица соответствия группе {ur_lico}'
    filter_data = Groups.objects.all().values('name')
    form = FilterChooseGroupForm(request.POST)
    import_data_error_text = ''
    for article_id in articles_data:
        if not ArticleGroup.objects.filter(common_article=article_id['pk']).exists():
            obj = ArticleGroup(
                common_article=Articles.objects.get(id=article_id['pk']))
            obj.save()
    data = ArticleGroup.objects.filter(
        common_article__company=ur_lico).order_by('common_article')
    if request.GET.get('checkbox_value') == 'true':
        data = ArticleGroup.objects.filter(
            common_article__company=ur_lico,
            group__isnull=True).order_by('common_article')

    if request.POST:
        if request.POST.get('export') == 'create_file':
            return excel_creating_mod(data)
        elif 'import_file' in request.FILES:
            import_data_error_text = excel_import_data(
                request.FILES['import_file'], ur_lico)
        elif 'filter' in request.POST:
            filter_data = request.POST
            article_filter = filter_data.get("common_article")
            group_filter = filter_data.get("group_name")

            if article_filter:
                if Articles.objects.filter(common_article=article_filter).exists():
                    data = ArticleGroup.objects.filter(
                        Q(common_article=Articles.objects.filter(common_article=article_filter)[0])).order_by('id')
                else:
                    data = ArticleGroup.objects.filter(
                        Q(common_article=0)).order_by('id')
            if group_filter:
                data = ArticleGroup.objects.filter(
                    Q(group=Groups.objects.filter(id=group_filter)[0])).order_by('id')
        elif 'group_name' in request.POST:
            if request.POST['change_group']:
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
        'ur_lico': ur_lico,
        'page_name': page_name,
        'import_data_error_text': import_data_error_text
    }
    return render(request, 'price_system/article_groups.html', context)


def ip_article_groups_view(request):
    """Отвечает за сопоставление артикула и группы ИП"""
    return article_groups_view(request, 'ИП Караваев')


def ooo_article_groups_view(request):
    """Отвечает за сопоставление артикула и группы ООО"""
    return article_groups_view(request, 'ООО Иннотрейд')


def gramoty_article_groups_view(request):
    """Отвечает за сопоставление артикула и группы Мастерская чудес"""
    return article_groups_view(request, 'ООО Мастерская чудес')


def article_price_statistic(request, ur_lico):
    """Отображает статистику по изменению цен артикулов"""

    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)
    data = ArticlesPrice.objects.filter(common_article__company=ur_lico,
                                        price_date__gte=start_date).order_by('common_article')
    price_date = ArticlesPrice.objects.filter(common_article__company=ur_lico,
                                              price_date__gte=start_date).values('price_date').distinct()
    article_list = Articles.objects.filter(
        company=ur_lico).order_by('common_article')
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


def ip_article_price_statistic(request):
    """Отображает статистику по изменениею цен артикулов ИП Караваев"""
    return article_price_statistic(request, 'ИП Караваев')


def ooo_article_price_statistic(request):
    """Отображает статистику по изменениею цен артикулов ООО Иннотрейд"""
    return article_price_statistic(request, 'ООО Иннотрейд')


def gramoty_article_price_statistic(request):
    """Отображает статистику по изменениею цен артикулов ООО Мастерская чудес"""
    return article_price_statistic(request, 'ООО Мастерская чудес')


class ArticleCompareDetailView(ListView):
    model = Articles
    template_name = 'price_system/article_compare_detail.html'
    context_object_name = 'data'

    def __init__(self, *args, **kwargs):
        self.ur_lico = kwargs.pop('ur_lico', None)
        super(ArticleCompareDetailView, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ArticleCompareDetailView,
                        self).get_context_data(**kwargs)
        print(kwargs)
        return context

    def post(self, request, *args, **kwargs):
        if request.POST:
            post_data = request.POST
            article = Articles.objects.get(company=self.ur_lico,
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
        return redirect('article_compare_detail_ooo', self.kwargs['common_article'])

    def get_queryset(self):
        common_article = self.kwargs['common_article']
        return Articles.objects.filter(company=self.ur_lico, common_article=common_article)


class ArticleCompareDetailInnotreid(ArticleCompareDetailView):
    def __init__(self, *args, **kwargs):
        super(ArticleCompareDetailInnotreid, self).__init__(*args, **kwargs)
        self.ur_lico = 'ООО Иннотрейд'


class ArticleCompareDetailKaravaev(ArticleCompareDetailView):
    def __init__(self, *args, **kwargs):
        super(ArticleCompareDetailKaravaev, self).__init__(*args, **kwargs)
        self.ur_lico = 'ИП Караваев'


class ArticleCompareDetailChudes(ArticleCompareDetailView):
    def __init__(self, *args, **kwargs):
        super(ArticleCompareDetailChudes, self).__init__(*args, **kwargs)
        self.ur_lico = 'ООО Мастерская Чудес'
