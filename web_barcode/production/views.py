from datetime import date, timedelta
import pandas as pd
from database.forms import SelectDateForm
from django.db.models import Q
import datetime
from django.shortcuts import redirect, render
from django.views.generic import DeleteView, DetailView, ListView, UpdateView

from .models import Delivery

def delivery_number(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    #if request.user.is_staff == True:
    data = Delivery.objects.all()
    today_raw = datetime.datetime.today()
    today = today_raw.strftime("%d.%m.%Y")
    description = Delivery.objects.values('production_date').distinct()
    print(description)
    context = {
        'data': data,
        'today': today
    }
    if request.method == 'POST':
        #print(list(request.POST.keys())[3])
        print(request.POST)
        
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
        new_data.save()

    elif request.method == 'POST' and request.FILES['myarticles']:
        myfile = request.FILES['myarticles']
        empexceldata = pd.read_excel(myfile)
        load_excel_data_wb_stock = pd.DataFrame(
            empexceldata, columns=['Предмет', 'Артикул поставщика',
                                   'Со склада', 'Количество'])
        subject_list = load_excel_data_wb_stock['Предмет'].to_list()
        supplier_article_list = load_excel_data_wb_stock['Артикул поставщика'].to_list()
        from_stock_list = load_excel_data_wb_stock['Со склада'].to_list()
        amount_list = load_excel_data_wb_stock['Количество'].to_list()
        dbframe = empexceldata

        for i in range(len(subject_list)):
            if Delivery.objects.filter(Q(subject=subject_list[i])):
                Delivery.objects.filter(supplier_article=supplier_article_list[i]).update(
                from_stock=from_stock_list[i],
                amount_list=amount_list[i],
                )
            else:
                obj = Delivery(
                subject=subject_list[i],
                supplier_article=supplier_article_list[i],
                from_stock=from_stock_list[i],
                amount=amount_list[i],
                )
                obj.save()
    
    return render(request, 'production/delivery_amount.html', context)