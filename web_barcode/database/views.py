from datetime import date, datetime, timedelta

import pandas as pd
import xlwt
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView, UpdateView
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from .forms import (ArticlesForm, LoginUserForm, SalesForm, SelectDateForm,
                    ShelvingForm, StocksForm)
from .models import (Articles, CodingMarketplaces, Sales, ShelvingStocks,
                     Stocks, WildberriesStocks)

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
    "Белые столбы": 27,
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
    "Товары в пути до клиента",
    "Товары в пути от клиента",
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
    "Белые столбы",
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
    if request.user.is_staff == True:
        print(request.user.is_staff)
        data = Articles.objects.all()
        context = {
            'data': data,
        }

        if request.method == 'POST' and request.FILES['myarticles']:
            myfile = request.FILES['myarticles']
            empexceldata = pd.read_excel(myfile)
            load_excel_data_wb_stock = pd.DataFrame(
                empexceldata, columns=['Общий артикул', 'Наш Артикул на WB (артикул поставщика)',
                                       'Barcode WB', 'Артикул WB (номенклатура)',
                                       'Наш Артикул на OZON (артикул поставщика)',
                                       'OZON Product ID', 'FBO OZON SKU ID',
                                       'FBS OZON SKU ID', 'Barcode OZON',
                                       'Наш Артикул на Яндекс (артикул поставщика)',
                                       'Barcode YANDEX', 'SKU на YANDEX'])
            common_article_list = load_excel_data_wb_stock['Общий артикул'].to_list()
            article_seller_wb_list = load_excel_data_wb_stock['Наш Артикул на WB (артикул поставщика)'].to_list()
            article_wb_nomenclature_list = load_excel_data_wb_stock['Артикул WB (номенклатура)'].to_list()
            barcode_wb_list = load_excel_data_wb_stock['Barcode WB'].to_list()
            article_seller_ozon_list = load_excel_data_wb_stock['Наш Артикул на OZON (артикул поставщика)'].to_list()
            ozon_product_id_list = load_excel_data_wb_stock['OZON Product ID'].to_list()
            fbo_ozon_sku_id_list = load_excel_data_wb_stock['FBO OZON SKU ID'].to_list()
            fbs_ozon_sku_id_list = load_excel_data_wb_stock['FBS OZON SKU ID'].to_list()
            barcode_ozon_list = load_excel_data_wb_stock['Barcode OZON'].to_list()
            article_seller_yandex_list = load_excel_data_wb_stock['Наш Артикул на Яндекс (артикул поставщика)'].to_list()
            barcode_yandex_list = load_excel_data_wb_stock['Barcode YANDEX'].to_list()
            sku_yandex_list = load_excel_data_wb_stock['SKU на YANDEX'].to_list()
            dbframe = empexceldata

            for i in range(len(common_article_list)):
                obj = Articles.objects.create(
                    common_article=common_article_list[i],
                    article_seller_wb=article_seller_wb_list[i],
                    article_wb_nomenclature=article_wb_nomenclature_list[i],
                    barcode_wb=barcode_wb_list[i],
                    article_seller_ozon=article_seller_ozon_list[i],
                    ozon_product_id=ozon_product_id_list[i],
                    fbo_ozon_sku_id=fbo_ozon_sku_id_list[i],
                    fbs_ozon_sku_id=fbs_ozon_sku_id_list[i],
                    barcode_ozon=barcode_ozon_list[i],
                    article_seller_yandex=article_seller_yandex_list[i],
                    barcode_yandex=barcode_yandex_list[i],
                    sku_yandex=sku_yandex_list[i],
                    )
            obj.save()
        return render(request, 'database/database_home.html', context)
    else:
        return redirect('home')


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
        list_name_seller_article = load_excel_data_wb_stock['Артикул продавца'].to_list()
        list_name_wb_article = load_excel_data_wb_stock['Артикул WB'].to_list()
        for i in empexceldata.columns.ravel():
            if i not in START_LIST:
                MUST_BE_EMPTY.append(i)
        if len(MUST_BE_EMPTY) == 0:
            dbframe = empexceldata
            for dbframe in dbframe.itertuples():
                for i in range(len(empexceldata.columns.ravel())):
                    for j in DICT_FOR_STOCKS_WB.keys():
                        if empexceldata.columns.ravel()[i] == j:
                            if 'school' not in list_name_seller_article[i] and (
                                    'diplom' not in list_name_seller_article[i]):
                                if str(dbframe[i+1]) == 'nan':
                                    continue
                                else:
                                    obj = WildberriesStocks.objects.create(
                                        seller_article_wb=list_name_seller_article[i],
                                        article_wb=list_name_wb_article[i],
                                        code_stock_id=int(DICT_FOR_STOCKS_WB[j]),
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
                Q(article_marketplace=article_filter))
    context = {
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
    #pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
    # ========== Печать PDF файла ========== #
    if request.method == 'GET' and 'to-my-pdf' in request.GET.keys():
        response = HttpResponse(content_type='application/pdf')
        pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
        response['Content-Disposition'] = 'attachment; filename="my_table.pdf"'
        doc = SimpleDocTemplate(response, pagesize=letter)
        data = []
        data.append(['Дата начала задачи', 'Артикул', 'Номер полки', 'Количество', 'Новое количество'])
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


def database_sales(request):
    """Отображение страницы База данных продаж"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    control_date_stock = date.today() - timedelta(days=1)
    seller_articles = Articles.objects.all()
    coding_marketplace = CodingMarketplaces.objects.all()
    data = Sales.objects.all()
    summa1 = Sales.objects.values('article_marketplace').annotate(
        Sum('amount'),
        Sum('sum_sale'),
        Sum('sum_pay'),

        avg=Sum('sum_sale')/Sum('amount')
        ).order_by('article_marketplace')
    summa = []
    for i in summa1:
        x = list(i.values())
        x.append(1)
        summa.append(x)

    form = SelectDateForm(request.POST or None)
    datestart = control_date_stock
    datefinish = control_date_stock

    if form.is_valid():
        datestart = form.cleaned_data.get("datestart")
        datefinish = form.cleaned_data.get("datefinish")
        article_filter = form.cleaned_data.get("article_filter")
        if article_filter == '':
            data = Sales.objects.filter(
                Q(pub_date__range=[datestart, datefinish]))
        else:
            data = Sales.objects.filter(
                Q(pub_date__range=[datestart, datefinish]),
                Q(article_marketplace=article_filter))
    context = {
        'form': form,
        'data': summa,
        'form_date': str(control_date_stock),
        'lenght': len(seller_articles.all().values()),
        'seller_articles': seller_articles.all().values(),
        'coding_marketplace': coding_marketplace.values()[0]['id']
    }

    if request.method == 'GET' and ('export' in request.GET.keys()):
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="users.xls"'

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Users')
        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True
        # Define the titles for columns
        columns = [
            'Дата',
            'Артикул маркетплейса',
            'Количество',
            'Средняя цена',
            'Сумма продажи',
            'Сумма выплат',
            'Маркетплейс',
        ]
        # Assign the titles for each cell of the header
        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)
        # Iterate through all movies
        font_style = xlwt.XFStyle()

        rows = data.values_list('pub_date',
                                'article_marketplace',
                                'amount', 'avg_price_sale',
                                'sum_sale',
                                'sum_pay',
                                'code_marketplace')

        # Define the data for each cell in the row
        for row in rows:
            row_num += 1
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)

        wb.save(response)
        return response
    return render(request, 'database/database_sales.html', context)


def export_movies_to_xlsx(request):
    """
    Downloads all movies as Excel file with a single worksheet
    """
    if request.method == 'POST':
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="users.xls"'

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Users')
        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True
        # Define the titles for columns
        columns = [
            'Дата',
            'Артикул маркетплейса',
            'Количество',
            'Средняя цена',
            'Сумма продажи',
            'Сумма выплат',
            'Маркетплейс',
        ]
        # Assign the titles for each cell of the header
        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)
        # Iterate through all movies
        font_style = xlwt.XFStyle()

        rows = Sales.objects.all().values_list('pub_date',
                                               'article_marketplace',
                                               'amount',
                                               'avg_price_sale',
                                               'sum_sale',
                                               'sum_pay',
                                               'code_marketplace')

        # Define the data for each cell in the row
        for row in rows:
            row_num += 1
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)

        wb.save(response)
        return response
    return render(request, 'database/database_sales.html')


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


class DatabaseSalesDetailView(ListView):
    model = Sales
    template_name = 'database/sales_detail.html'
    context_object_name = 'articles'

    def get_context_data(self, **kwargs):
        context = super(DatabaseSalesDetailView, self).get_context_data(**kwargs)
        context.update({
            'wbstocks': Stocks.objects.filter(
            article_marketplace=self.kwargs['article_marketplace']).values()
        })
        #print(Stocks.objects.filter(
        #    article_marketplace=self.kwargs['article_marketplace']).values())
        return context

    def get_queryset(self):
        #print(Sales.objects.filter(
        #    article_marketplace=self.kwargs['article_marketplace']).values())
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
        return reverse_lazy('home')


def logout_user(request):
    logout(request)
    return redirect('login')
