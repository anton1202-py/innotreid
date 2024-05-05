from datetime import date, datetime, timedelta

import pandas as pd
import xlwt
from celery import current_app
from celery_tasks.celery import app as celery_app
from celery_tasks.ozon_tasks import fbs_balance_maker_for_all_company
from database.ozon_supplyment import save_ozon_sale_data_for_motivation
from database.periodic_tasks import (process_ozon_sales_data,
                                     process_wb_sales_data)
from database.wb_supplyment import save_wildberries_sale_data_for_motivation
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Case, Count, IntegerField, Q, Sum, When
from django.db.models.functions import (ExtractMonth, ExtractWeek, ExtractYear,
                                        TruncWeek)
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView, UpdateView
from ozon_system.tasks import delete_ozon_articles_with_low_price_from_actions
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from .forms import (ArticlesForm, LoginUserForm, SalesForm, SelectArticlesForm,
                    SelectDateForm, SelectDateStocksForm, ShelvingForm,
                    StocksForm)
from .models import (Articles, CodingMarketplaces, OrdersFbsInfo, Sales,
                     ShelvingStocks, Stocks, Stocks_wb_frontend,
                     WildberriesStocks)

DICT_FOR_STOCKS_WB = {
    "Товары в пути до клиента": 1,
    "Товары в пути от клиента": 2,
    "Итого по складам": 3,
    "Подольск": 4,
    "Подольск 3": 5,
    "Коледино": 6,
    "Казань": 7,
    "Электросталь": 8,
    "Краснодар": 9,
    "Екатеринбург": 10,
    "Санкт-Петербург": 11,
    "Новосибирск": 12,
    "Хабаровск": 13,
    "Тула": 14,
    "Астана": 15,
    "Чехов": 16,
    "Белая Дача": 17,
    "Невинномысск": 18,
    "Домодедово": 19,
    "Вёшки": 20,
    "Минск": 21,
    "Пушкино": 22,
    "Внуково КБТ": 23,
    "Обухово": 24,
    "Остальные": 25,
    "Атакент": 26,
    "Белые Столбы": 27,
    "Иваново": 28
}

START_LIST = [
    "Бренд",
    "Предмет",
    "Артикул продавца",
    "Артикул WB",
    "Объем, л",
    "Баркод",
    "Размер вещи",
    "В пути до клиента",
    "В пути от клиента",
    "Итого по складам",
    "Подольск",
    "Подольск 3",
    "Коледино",
    "Казань",
    "Электросталь",
    "Краснодар",
    "Екатеринбург",
    "Санкт-Петербург",
    "Новосибирск",
    "Хабаровск",
    "Тула",
    "Астана",
    "Атакент",
    "Чехов",
    "Белая Дача",
    "Невинномысск",
    "Домодедово",
    "Белые Столбы",
    "Вёшки",
    "Минск",
    "Пушкино",
    "Иваново",
    "Внуково КБТ",
    "Обухово",
    "Остальные"
]


def database_home(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    # save_wildberries_sale_data_for_motivation()
    data = Articles.objects.all()
    context = {
        'data': data,
    }
    return render(request, 'database/database_home.html', context)


def article_compare(request):
    data = Articles.objects.all()
    form = SelectArticlesForm(request.POST or None)
    article_data = []

    if request.method == 'POST' and form.is_valid():
        articles_filter = form.cleaned_data.get("article_filter")
        articles_list = articles_filter.split()
        for article in articles_list:
            filtered_article = Articles.objects.filter(
                Q(common_article=article))
            article_data.append(filtered_article)
    context = {

        'article_data': article_data,
        'data': data.all().values(),
    }
    return render(request, 'database/article_compare.html', context)


def database_stock(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    control_date_stock = date.today() - timedelta(days=1)
    x = Articles.objects.all()
    data = Stocks.objects.filter(Q(pub_date__range=[
        control_date_stock,
        control_date_stock]))
    form = SelectDateForm(request.POST or None)
    datestart = control_date_stock
    datefinish = control_date_stock
    if request.method == 'POST' and (len(request.POST.keys()) == 1):
        myfile = request.FILES['myfile']
        empexceldata = pd.read_excel(myfile)
        dbframe = empexceldata
        for dbframe in dbframe.itertuples():
            if 'school' not in dbframe.seller_article and (
                    'diplom' not in dbframe.seller_article):
                if str(dbframe.Количество) == 'nan':
                    obj = Stocks.objects.create(
                        article_marketplace=dbframe.seller_article,
                        code_marketplace_id=1,
                        amount=0
                    )
                else:
                    obj = Stocks.objects.create(
                        article_marketplace=dbframe.seller_article,
                        code_marketplace_id=1,
                        amount=dbframe.Количество
                    )
                obj.save()
    elif form.is_valid():
        datestart = form.cleaned_data.get("datestart")
        datefinish = form.cleaned_data.get("datefinish")
        article_filter = form.cleaned_data.get("article_filter")
        if article_filter == '':
            data = Stocks.objects.filter(
                Q(pub_date__range=[datestart, datefinish]))
        else:
            data = Stocks.objects.filter(
                Q(pub_date__range=[datestart, datefinish]),
                Q(article_marketplace=article_filter))
    context = {
        'form': form,
        'data': data,
        'datestart': str(datestart),
        'x': x.all().values(),
    }
    return render(request, 'database/database_stock.html', context)


def database_stock_wb(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    control_date_stock = date.today() - timedelta(days=1)
    x = Articles.objects.all()
    data = WildberriesStocks.objects.filter(Q(pub_date__range=[
        control_date_stock,
        control_date_stock]))
    form = SelectDateForm(request.POST or None)
    datestart = control_date_stock
    datefinish = control_date_stock
    if request.method == 'POST' and (len(request.POST.keys()) == 1):
        MUST_BE_EMPTY = []
        myfile = request.FILES['myfile']
        empexceldata = pd.read_excel(myfile)
        load_excel_data_wb_stock = pd.DataFrame(
            empexceldata, columns=['Артикул продавца', 'Артикул WB'])
        list_name_seller_article = load_excel_data_wb_stock['Артикул продавца'].to_list(
        )
        list_name_wb_article = load_excel_data_wb_stock['Артикул WB'].to_list()

        for i in empexceldata.columns.ravel():
            if i not in START_LIST:
                MUST_BE_EMPTY.append(i)
        if len(MUST_BE_EMPTY) == 0:
            dbframe = empexceldata
            for dbframe in dbframe.itertuples():
                print(dbframe)
                for i in range(len(empexceldata.columns.ravel())):

                    for j in DICT_FOR_STOCKS_WB.keys():
                        # empexceldata.columns.ravel()[i] - название столбцов в excel файле
                        if empexceldata.columns.ravel()[i] == j:
                            if 'school' not in dbframe[3] and (
                                    'diplom' not in dbframe[3]):
                                if str(dbframe[i+1]) == 'nan':
                                    continue
                                else:

                                    obj = WildberriesStocks.objects.create(
                                        seller_article_wb=dbframe[3],
                                        article_wb=dbframe[4],
                                        code_stock_id=int(
                                            DICT_FOR_STOCKS_WB[empexceldata.columns.ravel()[i]]),
                                        amount=dbframe[i+1],
                                    )
                                    obj.save()
        else:
            result = " ".join(MUST_BE_EMPTY)
            mes = f'В файле от Wildberries добавились столбцы: {result}'
            messages.error(request, mes)
    elif form.is_valid():
        datestart = form.cleaned_data.get("datestart")
        datefinish = form.cleaned_data.get("datefinish")
        article_filter = form.cleaned_data.get("article_filter")
        if article_filter == '':
            data = WildberriesStocks.objects.filter(
                Q(pub_date__range=[datestart, datefinish]))
        else:
            data = WildberriesStocks.objects.filter(
                Q(pub_date__range=[datestart, datefinish]),
                Q(seller_article_wb=article_filter))
    stocks_names = WildberriesStocks.objects.values_list(
        'code_stock', flat=True).distinct()
    context = {
        'stocks_list': DICT_FOR_STOCKS_WB.keys(),
        'stocks_names': stocks_names,
        'range': range(len(data)),
        'data': data,
        'lenght': len(x.all().values()),
        'x': x.all().values(),
    }
    return render(request, 'database/database_stock_wb.html', context)


def database_stock_shelving(request):
    """Функция отвечает за страницу склада стеллажей"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    innotreid_articles = Articles.objects.all()
    data = ShelvingStocks.objects.all()
    two_days_ago = datetime.now() - timedelta(days=2)
    # ========== Выдает таблицу, отфильтрованную по количеству от 0 до 3
    task_data = ShelvingStocks.objects.filter(
        amount__range=(0, 3)).order_by('task_start_date')
    # ========== Выдает таблицу, отфильтрованную по количеству больше 4
    # и время завершения задания не равно None и запись младше 2 дней
    task_data_finish = ShelvingStocks.objects.filter(
        amount__gte=4).exclude(
        task_finish_date=None).exclude(
        task_finish_date__lte=two_days_ago).order_by('-task_finish_date')
    # pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
    # ========== Печать PDF файла ========== #
    if request.method == 'GET' and 'to-my-pdf' in request.GET.keys():
        response = HttpResponse(content_type='application/pdf')
        pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
        response['Content-Disposition'] = 'attachment; filename="my_table.pdf"'
        doc = SimpleDocTemplate(response, pagesize=letter)
        data = []
        data.append(['Дата начала задачи', 'Артикул',
                    'Номер полки', 'Количество', 'Новое количество'])
        for item in task_data:
            item.task_start_date = item.task_start_date + timedelta(hours=3)
            table_time = item.task_start_date.strftime("%Y-%m-%d %H:%M:%S")
            data.append([table_time,
                         item.seller_article,
                         item.shelf_number,
                         item.amount,])
        styles = getSampleStyleSheet()
        style_table = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Arial'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Arial'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ])
        table = Table(data)
        table.setStyle(style_table)
        doc.build([table])
        return response
    # ========== Конец печати PDF файла ========== #

    if request.method == 'POST' and (len(request.POST.keys()) == 1):
        myfile = request.FILES['myfile']
        empexceldata = pd.read_excel(myfile)
        dbframe = empexceldata
        for dbframe in dbframe.itertuples():
            obj = ShelvingStocks(
                seller_article_wb=dbframe.Артикул_ВБ,
                seller_article=dbframe.Артикул,
                shelf_number=dbframe.Ячейка,
                amount=dbframe.Количество,
            )
            obj.save()
    elif request.method == 'POST':
        quantity = int(list(request.POST.values())[1])
        for i in range(len(data.values())):
            if int(list(request.POST.keys())[1]) in data.values()[i].values():
                id_data = ShelvingStocks.objects.get(
                    id=list(request.POST.keys())[1]).pk
                article_data = ShelvingStocks.objects.get(
                    id=list(request.POST.keys())[1]).seller_article_wb
                new_data = ShelvingStocks.objects.get(
                    id=id_data)
                new_data.amount = int(list(request.POST.values())[1])
                new_data.task_finish_date = datetime.now()
                new_data.save()
    context = {
        'task_data': task_data,
        'data': task_data_finish,
        'lenght': len(innotreid_articles.all().values()),
        'x': innotreid_articles.all().values(),
    }
    return render(request, 'database/database_stock_shelving.html', context)


def stock_frontend(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    control_date_stock = date.today()  # - timedelta(days=1)
    data = Stocks_wb_frontend.objects.filter(Q(pub_date__range=[
        control_date_stock,
        control_date_stock]))
    form = SelectDateStocksForm(request.POST or None)
    datestart = control_date_stock
    datefinish = control_date_stock

    if form.is_valid():
        datestart = form.cleaned_data.get("datestart")
        datefinish = form.cleaned_data.get("datefinish")
        article_filter = form.cleaned_data.get("article_filter")
        stock_filter = form.cleaned_data.get("stock_filter")
        if article_filter == '' and stock_filter == '':
            data = Stocks_wb_frontend.objects.filter(
                Q(pub_date__range=[datestart, datefinish]))
        elif article_filter != '' and stock_filter == '':
            data = Stocks_wb_frontend.objects.filter(
                Q(pub_date__range=[datestart, datefinish]),
                Q(seller_article_wb=article_filter))
        elif article_filter == '' and stock_filter != '':
            data = Stocks_wb_frontend.objects.filter(
                Q(pub_date__range=[datestart, datefinish]),
                Q(stock_name=stock_filter))
        else:
            data = Stocks_wb_frontend.objects.filter(
                Q(pub_date__range=[datestart, datefinish]),
                Q(seller_article_wb=article_filter),
                Q(stock_name=stock_filter))
    context = {
        'form': form,
        'data': data,
        'datestart': str(datestart),
    }
    return render(request, 'database/stock_frontend.html', context)


def database_sales(request):
    """Отображение страницы База данных продаж"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    datestart = date.today() - timedelta(days=7)
    datefinish = date.today() - timedelta(days=1)
    data = Sales.objects.filter(
        Q(pub_date__range=[datestart, datefinish])
    ).values('article_marketplace').annotate(
        summ_sale=Sum('sum_sale'),
        summ_pay=Sum('sum_pay'),
        avg=Sum('sum_pay')/Sum('amount'),
        total=Sum('amount')
    ).order_by('-total')
    orders_count = Sales.objects.filter(
        Q(pub_date__range=[datestart, datefinish])
    ).values('article_marketplace').aggregate(total=Sum('amount'))
    form = SelectDateForm(request.POST or None)

    if form.is_valid():
        datestart = form.cleaned_data.get("datestart")
        datefinish = form.cleaned_data.get("datefinish")
        article_filter = form.cleaned_data.get("article_filter")
        if article_filter == '':
            data = Sales.objects.filter(
                Q(pub_date__range=[datestart, datefinish])
            ).values('article_marketplace').annotate(
                summ_sale=Sum('sum_sale'),
                summ_pay=Sum('sum_pay'),
                avg=Sum('sum_sale')/Sum('amount'),
                total=Sum('amount')
            ).order_by('-total')
            orders_count = Sales.objects.filter(
                Q(pub_date__range=[datestart, datefinish])
            ).values('article_marketplace').aggregate(total=Sum('amount'))
        else:
            data = Sales.objects.filter(
                Q(pub_date__range=[datestart, datefinish]),
                Q(article_marketplace=article_filter)
            ).values('article_marketplace').annotate(
                summ_sale=Sum('sum_sale'),
                summ_pay=Sum('sum_pay'),
                avg=Sum('sum_sale')/Sum('amount'),
                total=Sum('amount')
            ).order_by('-total')
            orders_count = Sales.objects.filter(
                Q(pub_date__range=[datestart, datefinish]),
                Q(article_marketplace=article_filter)
            ).values('article_marketplace').aggregate(total=Sum('amount'))
    context = {
        'form': form,
        'data': data,
        'form_date': str(datestart),
        'date_finish': str(datefinish),
        'orders_count': orders_count
    }
    return render(request, 'database/database_sales.html', context)


def analytic_sales_data(request):
    """Функция отвечает за отображение данных недельных продаж"""

    sales = Sales.objects.filter(sum_sale__gte=0).annotate(
        week=ExtractWeek('pub_date'),
        year=ExtractYear('pub_date')
    ).values('article_marketplace', 'week', 'year').annotate(
        count=Count(Case(When(sum_sale__gte=0, then=1),
                    output_field=IntegerField()))
    ).order_by('article_marketplace', 'year', 'week')

    articles_amount = Sales.objects.filter(sum_sale__gte=0).annotate(
        week=TruncWeek('pub_date')
    ).values('week').annotate(
        count=Count('article_marketplace')
    ).order_by('week')

    sales_data = Sales.objects.filter(sum_sale__gte=0).annotate(
        week=ExtractWeek('pub_date'),
        year=ExtractYear('pub_date')
    ).values('week', 'year').order_by('year', 'week')

    # Создаем словарь с данными для передачи в шаблон
    data = {}
    week_data = []
    for tim in sales_data:

        week_year = f"{tim['week']}-{tim['year']}"
        week_data.append(week_year)

    unique_week = list(set(week_data))
    unique_week.sort()

    for sale in sales:
        supplier_article = sale['article_marketplace']
        week_year = f"{sale['week']}-{sale['year']}"
        count = sale['count']
        if supplier_article not in data:
            data[supplier_article] = {}
        data[supplier_article][week_year] = count

    # Добавляем недостающие недели со значением 0
    for article_data in data.values():
        for week in unique_week:
            if week not in article_data:
                article_data[week] = 0

    context = {
        'data': data,
        'unique_week': unique_week,
        'articles_amount': articles_amount,
    }
    return render(request, 'database/sales_analytic.html', context)


def database_orders_fbs(request):
    """Отображение страницы База данных продаж"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')

    # Вычисляем сумму заказанных артикулов
    form = SelectDateForm(request.POST or None)
    datestart = date.today() - timedelta(days=7)
    datefinish = date.today() - timedelta(days=1)

    data = OrdersFbsInfo.objects.filter(
        Q(pub_date__range=[datestart, datefinish])
    ).values('article_marketplace').annotate(total=Sum('amount')
                                             ).order_by('-total')
    orders_count = OrdersFbsInfo.objects.filter(
        Q(pub_date__range=[datestart, datefinish])
    ).values('article_marketplace').aggregate(total=Sum('amount'))
    if form.is_valid():
        datestart = form.cleaned_data.get("datestart")
        datefinish = form.cleaned_data.get("datefinish")
        article_filter = form.cleaned_data.get("article_filter")
        if article_filter == '':
            raw_data = OrdersFbsInfo.objects.filter(
                Q(pub_date__range=[datestart, datefinish]))
            data = raw_data.values('article_marketplace').annotate(
                total=Sum('amount')).order_by('-total')
            orders_count = OrdersFbsInfo.objects.filter(
                Q(pub_date__range=[datestart, datefinish])
            ).values('article_marketplace').aggregate(total=Sum('amount'))
        else:
            data = OrdersFbsInfo.objects.filter(
                Q(pub_date__range=[datestart, datefinish]),
                Q(article_marketplace=article_filter)
            ).values('article_marketplace').annotate(total=Sum('amount')
                                                     ).order_by('-total')
            orders_count = OrdersFbsInfo.objects.filter(
                Q(pub_date__range=[datestart, datefinish]),
                Q(article_marketplace=article_filter)
            ).values('article_marketplace').aggregate(total=Sum('amount'))

    context = {
        'form': form,
        'data': data,
        'form_date': str(datestart),
        'date_finish': str(datefinish),
        'orders_count': orders_count
    }

    return render(request, 'database/database_orders_fbs.html', context)


class DatabaseDetailView(DetailView):
    model = Articles
    template_name = 'database/detail_view.html'
    context_object_name = 'article'


class DatabaseStockDetailView(ListView):
    model = Stocks
    template_name = 'database/stock_detail.html'
    context_object_name = 'articles'

    def get_queryset(self):
        return Stocks.objects.filter(
            article_marketplace=self.kwargs['article_marketplace'])


class DatabaseStockFrontendDetailView(ListView):
    model = Stocks_wb_frontend
    template_name = 'database/stock_frontend_detail.html'
    context_object_name = 'articles'

    def get_queryset(self):
        return Stocks_wb_frontend.objects.filter(
            seller_article_wb=self.kwargs['seller_article_wb'])


class DatabaseSalesDetailView(ListView):
    model = Sales
    template_name = 'database/sales_detail.html'
    context_object_name = 'articles'

    def get_context_data(self, **kwargs):
        context = super(DatabaseSalesDetailView,
                        self).get_context_data(**kwargs)
        context.update({
            'wbstocks': Stocks.objects.filter(
                article_marketplace=self.kwargs['article_marketplace']).values()
        })
        return context

    def get_queryset(self):
        return Sales.objects.filter(
            article_marketplace=self.kwargs['article_marketplace'])


class DatabaseSalesAnalyticDetailView(ListView):
    model = Sales
    template_name = 'database/sales_analytic_detail.html'
    context_object_name = 'articles'

    def get_context_data(self, **kwargs):
        context = super(DatabaseSalesAnalyticDetailView,
                        self).get_context_data(**kwargs)

        sales = Sales.objects.filter(
            Q(article_marketplace=self.kwargs['article_marketplace']),
            Q(sum_sale__gte=0)).annotate(
                week=ExtractWeek('pub_date'),
                year=ExtractYear('pub_date')
        ).values('article_marketplace', 'week', 'year').annotate(
                count=Count(Case(When(sum_sale__gte=0, then=1),
                            output_field=IntegerField()))
        ).order_by('article_marketplace', 'year', 'week')

        sales_data = Sales.objects.filter(
            Q(sum_sale__gte=0)).annotate(
                week=ExtractWeek('pub_date'),
                year=ExtractYear('pub_date')
        ).values('week', 'year').order_by('year', 'week')
        data = {}
        week_data = []
        for tim in sales_data:

            week_year = f"{tim['week']}-{tim['year']}"
            week_data.append(week_year)

        unique_week = list(set(week_data))
        unique_week.sort()

        for sale in sales:
            supplier_article = sale['article_marketplace']
            week_year = f"{sale['week']}-{sale['year']}"
            count = sale['count']
            if supplier_article not in data:
                data[supplier_article] = {}
            data[supplier_article][week_year] = count

        # Добавляем недостающие недели со значением 0
        for article_data in data.values():
            for week in unique_week:
                if week not in article_data:
                    article_data[week] = 0
        context.update({
            'data': data,
            'unique_week': unique_week,
        })
        return context

    def get_queryset(self):
        return Sales.objects.filter(
            article_marketplace=self.kwargs['article_marketplace'])


class DatabaseUpdateView(UpdateView):
    model = Articles
    template_name = 'database/create.html'
    form_class = ArticlesForm


class DatabaseStockUpdateView(UpdateView):
    model = Stocks
    template_name = 'database/create_stock.html'
    form_class = StocksForm


class DatabaseShelvingUpdateView(UpdateView):
    model = ShelvingStocks
    template_name = 'database/shelving_update.html'
    form_class = ShelvingForm


class DatabaseSalesUpdateView(UpdateView):
    model = Sales
    template_name = 'database/create_sales.html'
    form_class = SalesForm


class DatabaseDeleteView(DeleteView):
    model = Articles
    template_name = 'database/database_delete.html'
    success_url = '/stock/'


class DatabaseStockDeleteView(DeleteView):
    model = Stocks
    template_name = 'database/stock_delete.html'
    success_url = '/stock/'


class DatabaseSalesDeleteView(DeleteView):
    model = Sales
    template_name = 'database/sales_delete.html'
    success_url = '/sales/'


@login_required
def create(request):
    error = ''
    if request.method == 'POST':
        form = ArticlesForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('database_home')
        else:
            error = 'Форма была не верной'
    form = ArticlesForm()
    data = {
        'form': form,
        'error': error
    }
    return render(request, 'database/create.html', data)


@login_required
def create_stock(request):
    error = ''
    if request.method == 'POST':
        form = StocksForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('database_stock')
        else:
            error = 'Форма была не верной'
    form = StocksForm()
    data = {
        'form': form,
        'error': error
    }
    return render(request, 'database/create_stock.html', data)


@login_required
def create_shelving_stocks(request):
    error = ''
    if request.method == 'POST':
        form = ShelvingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('stock-shelving')
        else:
            error = 'Форма была не верной'
    form = ShelvingForm()
    data = {
        'form': form,
        'error': error
    }
    return render(request, 'database/create_shelving.html', data)


@login_required
def create_sales(request):
    error = ''
    if request.method == 'POST':
        form = SalesForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('database_sales')
        else:
            error = 'Форма была не верной'
    form = SalesForm()
    data = {
        'form': form,
        'error': error
    }
    return render(request, 'database/create_sales.html', data)


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'database/login.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        return dict(list(context.items()))

    def get_success_url(self):
        return reverse_lazy('database_home')


def logout_user(request):
    logout(request)
    return redirect('login')
