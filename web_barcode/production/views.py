from datetime import date, timedelta
import pandas as pd
from database.forms import SelectDateForm
from django.db.models import Q
import datetime
from django.shortcuts import redirect, render
from django.views.generic import DeleteView, DetailView, ListView, UpdateView

from .models import ArticlesDelivery, Delivery, ProductionDelivery



def product_detail(request):
    
    data = ArticlesDelivery.objects.all()
    data_id = ArticlesDelivery.objects.values_list('id', flat=True)
    production_amount = ProductionDelivery.objects.all()

    production_test = []
    for j in data_id:
        production_test.append(ProductionDelivery.objects.filter(articles=j)[0])

    today = datetime.datetime.today().strftime("%d-%m-%Y")

    description = ProductionDelivery.objects.values('production_date').distinct()
    production_date_raw = []
    for i in description:
        if i['production_date'] != None:
            date_object = datetime.datetime.strptime(str(i['production_date']), '%Y-%m-%d')
            formatted_date_new = date_object.strftime('%d-%m-%Y')
            production_date_raw.append(str(formatted_date_new))
    production_date = sorted(str(datetime.datetime.strptime(x, '%d-%m-%Y').strftime('%d-%m-%Y')) for x in production_date_raw)

    if str(today) not in production_date:
        for i in data_id:
            article_id = ArticlesDelivery.objects.get(id=i)
            obj = ProductionDelivery(
            articles=article_id,
            production_date=datetime.datetime.today().strftime("%Y-%m-%d"),
            day_quantity=0,
            night_quantity=0,
            )
            obj.save()

        description = ProductionDelivery.objects.values('production_date').distinct()
    production_date_raw = []
    for i in description:
        if i['production_date'] != None:
            date_object = datetime.datetime.strptime(str(i['production_date']), '%Y-%m-%d')
            formatted_date_new = date_object.strftime('%d-%m-%Y')
            production_date_raw.append(str(formatted_date_new))
    production_date = sorted(str(datetime.datetime.strptime(x, '%d-%m-%Y').strftime('%Y-%m-%d')) for x in production_date_raw)

    if request.method == 'POST' and request.FILES:
        myfile = request.FILES['myarticles']
        empexceldata = pd.read_excel(myfile)
        load_excel_data_wb_stock = pd.DataFrame(
            empexceldata, columns=['Предмет', 'Артикул поставщика',
                                   'Со склада', 'Количество', 'Фактическое количество'])
        subject_list = load_excel_data_wb_stock['Предмет'].to_list()
        supplier_article_list = load_excel_data_wb_stock['Артикул поставщика'].to_list()
        from_stock_list = load_excel_data_wb_stock['Со склада'].to_list()
        amount_list = load_excel_data_wb_stock['Количество'].to_list()
        dbframe = empexceldata

        for i in range(len(subject_list)):
            if ArticlesDelivery.objects.filter(Q(subject=subject_list[i])):
                ArticlesDelivery.objects.filter(supplier_article=supplier_article_list[i]).update(
                from_stock=from_stock_list[i],
                amount=amount_list[i],
                )
            else:
                obj = ArticlesDelivery(
                subject=subject_list[i],
                supplier_article=supplier_article_list[i],
                from_stock=from_stock_list[i],
                amount=amount_list[i],
                )
                obj.save()
    elif request.method == 'POST':
        #article_id = ArticlesDelivery.objects.get(id=list(request.POST.keys())[3])
        article_id = list(request.POST.keys())[3]
        date_for_production = list(request.POST.keys())[1][:10]
        date_object = datetime.datetime.strptime(date_for_production, '%Y-%m-%d')
        formatted_date = date_object.strftime('%Y-%m-%d')
        article = list(request.POST.keys())[1]
        
        for_data = article.split(", ")
        for_data_id = ArticlesDelivery.objects.get(supplier_article=for_data[2])
        if ProductionDelivery.objects.filter(Q(id=article_id)):
            ProductionDelivery.objects.filter(id=article_id).update(
            #articles = for_data_id,
            day_quantity=list(request.POST.values())[1],
            night_quantity=list(request.POST.values())[2],
            )
            
        else:
            obj = ProductionDelivery(
            id=article_id,
            articles = for_data_id,
            production_date=formatted_date,
            day_quantity=list(request.POST.values())[1],
            night_quantity=list(request.POST.values())[2],
            )
            obj.save()

    context = {
        'data': data,
        'production_test':production_test,
        'production_date': production_date,
        'today': today,
        'production_amount': production_amount
    }
    return render(request, 'production/delivery_data.html', context)



def delivery_number(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    #if request.user.is_staff == True:
    data = Delivery.objects.all().order_by('supplier_article')
    today_raw = datetime.datetime.today()
    today = today_raw.strftime("%d-%m-%Y")
    description = Delivery.objects.values('production_date').distinct()

    production_date = []
    for i in description:
        if i['production_date'] != None:
            production_date.append(i['production_date'])

    context = {
        'production_date': production_date,
        'data': data,
        'today': today
    }
    if request.method == 'POST' and request.FILES:
        myfile = request.FILES['myarticles']
        empexceldata = pd.read_excel(myfile)
        load_excel_data_wb_stock = pd.DataFrame(
            empexceldata, columns=['Предмет', 'Артикул поставщика',
                                   'Со склада', 'Количество', 'Фактическое количество'])
        subject_list = load_excel_data_wb_stock['Предмет'].to_list()
        supplier_article_list = load_excel_data_wb_stock['Артикул поставщика'].to_list()
        from_stock_list = load_excel_data_wb_stock['Со склада'].to_list()
        amount_list = load_excel_data_wb_stock['Количество'].to_list()
        fact_amount_list = load_excel_data_wb_stock['Фактическое количество'].to_list()
        dbframe = empexceldata

        for i in range(len(subject_list)):

            if str(fact_amount_list[i]) == 'nan':
                fact_amount_list[i] = ''
            if Delivery.objects.filter(Q(subject=subject_list[i])):
                Delivery.objects.filter(supplier_article=supplier_article_list[i]).update(
                from_stock=from_stock_list[i],
                amount=amount_list[i],
                fact_amount=fact_amount_list[i],
                )
            else:
                obj = Delivery(
                subject=subject_list[i],
                supplier_article=supplier_article_list[i],
                from_stock=from_stock_list[i],
                amount=amount_list[i],
                fact_amount=fact_amount_list[i],
                )
                obj.save()
    elif request.method == 'POST':
        delivery_id = Delivery.objects.get(id=list(request.POST.keys())[3]).pk
        new_data = Delivery.objects.get(id=list(request.POST.keys())[3])
        new_data.production_date = today_raw
        for i in request.POST.keys():
            if 'day' in i:
                if request.POST[i]:
                    new_data.day_production_amount = request.POST[i]
            elif 'night' in i:
                if request.POST[i]:
                    new_data.night_production_amount = request.POST[i]
        if new_data.night_production_amount and new_data.day_production_amount:
            new_data.fact_amount = f'{str(int(new_data.night_production_amount) + int(new_data.day_production_amount))}/{new_data.amount}'
        elif new_data.night_production_amount and not new_data.day_production_amount:
            new_data.fact_amount = f'{int(new_data.night_production_amount)}/{new_data.amount}'
        elif not new_data.night_production_amount and new_data.day_production_amount:
            new_data.fact_amount = f'{int(new_data.day_production_amount)}/{new_data.amount}'
        new_data.save()
    
    return render(request, 'production/delivery_amount.html', context)