import datetime

import pandas as pd
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TaskCreatorForm
from .models import ArticlesDelivery, ProductionDelivery, TaskCreator


def task_creation(request):
    """Описывает страницу создания заявок для производства"""
    data = TaskCreator.objects.all().order_by('id')

    form = TaskCreatorForm(request.POST or None)

    data_ids = data.values_list('id', flat=True)

    for i in data_ids:
        task_id = TaskCreator.objects.get(id=i)
        if ArticlesDelivery.objects.filter(task=task_id) and ProductionDelivery.objects.filter(task=task_id):
            production_amount = task_id.productiondelivery_set.all()
            
            articles_amount = task_id.articlesdelivery_set.all()
            articles_data = ArticlesDelivery.objects.filter(task=task_id)
            production_data = ProductionDelivery.objects.filter(task=task_id)

            percent_counter = 0
            data_id = ArticlesDelivery.objects.filter(task=task_id).values_list('id', flat=True)
            for j in data_id:
                if articles_data.get(id=j).amount <= production_data.filter(articles=j)[0].total_production:
                    percent_counter += 1

            article_total = articles_amount.aggregate(
                    sum=Sum('amount'))['sum']
            total_production = production_amount.aggregate(
                    sum=Sum('night_quantity')+Sum('day_quantity'))['sum'] + articles_amount.aggregate(
                    sum=Sum('from_stock'))['sum']
            data.filter(id=i).update(
                    remainder=f'{total_production}/{article_total}',
                    progress=f'{100*percent_counter//len(articles_amount)}%'
                    )
        else:
            data.filter(id=i).update(
                    remainder='0/0',
                    progress='0%'
                    )
    if request.method == 'POST' and 'button_task_id' in request.POST.keys():
        keys = request.POST.keys()
        printing = 'printing' in keys
        printed = 'printed' in keys
        shipment_status = 'shipment_status' in keys

        update_data = {
            'printing': printing,
            'printed': printed,
            'shipment_status': shipment_status
        }

        TaskCreator.objects.filter(id=int(request.POST['button_task_id'])).update(**update_data)
    #if request.method == 'POST' and 'button_task_id' in request.POST.keys():
    #    if 'printing' in request.POST.keys() and 'printed' in request.POST.keys() and 'shipment_status'  in request.POST.keys():
    #        TaskCreator.objects.filter(id=int(request.POST['button_task_id'])).update(
    #            printing=True,
    #            printed=True,
    #            shipment_status=True
    #            )
    #    elif not 'printing' in request.POST.keys() and not 'printed' in request.POST.keys() and not 'shipment_status'  in request.POST.keys():
    #        TaskCreator.objects.filter(id=int(request.POST['button_task_id'])).update(
    #            printing=False,
    #            printed=False,
    #            shipment_status=False
    #            )
    #    elif 'printing' in request.POST.keys() and not 'printed' in request.POST.keys() and not 'shipment_status'  in request.POST.keys():
    #        TaskCreator.objects.filter(id=int(request.POST['button_task_id'])).update(
    #            printing=True,
    #            printed=False,
    #            shipment_status=False
    #            )
    #    elif 'printing' in request.POST.keys() and 'printed' in request.POST.keys() and not 'shipment_status'  in request.POST.keys():
    #        TaskCreator.objects.filter(id=int(request.POST['button_task_id'])).update(
    #            printing=True,
    #            printed=True,
    #            shipment_status=False
    #            )
    #    elif 'printing' in request.POST.keys() and not 'printed' in request.POST.keys() and 'shipment_status'  in request.POST.keys():
    #        TaskCreator.objects.filter(id=int(request.POST['button_task_id'])).update(
    #            printing=True,
    #            printed=False,
    #            shipment_status=True
    #            )
    #    elif not 'printing' in request.POST.keys() and 'printed' in request.POST.keys() and not 'shipment_status'  in request.POST.keys():
    #        TaskCreator.objects.filter(id=int(request.POST['button_task_id'])).update(
    #            printing=False,
    #            printed=True,
    #            shipment_status=False
    #            )
    #    elif not 'printing' in request.POST.keys() and 'printed' in request.POST.keys() and 'shipment_status'  in request.POST.keys():
    #        TaskCreator.objects.filter(id=int(request.POST['button_task_id'])).update(
    #            printing=False,
    #            printed=True,
    #            shipment_status=True
    #            )
    #    elif not 'printing' in request.POST.keys() and not 'printed' in request.POST.keys() and 'shipment_status'  in request.POST.keys():
    #        TaskCreator.objects.filter(id=int(request.POST['button_task_id'])).update(
    #            printing=False,
    #            printed=False,
    #            shipment_status=True
    #            )

    if request.method == 'POST' and form.is_valid():
        task_name = form.cleaned_data.get("task_name")
        market_name = form.cleaned_data.get("market_name")
        obj = TaskCreator(
            task_name=task_name,
            market_name=market_name,
            )
        obj.save()
        return redirect('task_creation')
    
    if request.method == 'POST' and 'button_add_shipment_date' in request.POST.keys():
        id_d = request.POST['button_add_shipment_date']
        data.filter(id=request.POST['button_add_shipment_date']).update(
                    shipping_date=request.POST['add_shipment_date_name']
                    )
    elif request.method == 'POST' and 'del_delivery_button' in request.POST.keys():
        ProductionDelivery.objects.filter(task=request.POST['del_delivery_button']).delete()
        ArticlesDelivery.objects.filter(task=request.POST['del_delivery_button']).delete()
        TaskCreator.objects.filter(id=request.POST['del_delivery_button']).delete()
        return redirect('task_creation')
    
    context = {
        'data': data,
        'form': form
    }

    return render(request, 'production/add_delivery_number.html', context)


def product_detail(request, task_id):
    """Описывает страницу с артикулами в поставке. Их пополнение операторами."""
    
    task = get_object_or_404(TaskCreator, id=task_id)

    data = ArticlesDelivery.objects.filter(task=task)
    data_id = data.values_list('id', flat=True)
    production_amount = ProductionDelivery.objects.filter(task=task)

    today = datetime.datetime.today().strftime("%d-%m-%Y")

    description = production_amount.values('production_date').distinct()
    production_date_raw = []
    for i in description:
        if i['production_date'] != None:
            date_object = datetime.datetime.strptime(str(i['production_date']), '%Y-%m-%d')
            formatted_date_new = date_object.strftime('%d-%m-%Y')
            production_date_raw.append(str(formatted_date_new))
    production_date = sorted(str(datetime.datetime.strptime(x, '%d-%m-%Y').strftime('%d-%m-%Y')) for x in production_date_raw)

    compare_necessary_amount_and_production_amount = []
    for i in data_id:
        if production_amount.filter(articles=i):
            if data.get(id=i).amount > production_amount.filter(articles=i)[0].total_production:
                compare_necessary_amount_and_production_amount.append(False)
        else:
            compare_necessary_amount_and_production_amount.append(False)
    # Условие добавления нового дня в таблицу
    if str(today) not in production_date and False in compare_necessary_amount_and_production_amount:
        for i in data_id:
            article_id = ArticlesDelivery.objects.get(id=i)
            obj = ProductionDelivery(
            task=task,
            articles=article_id,
            production_date=datetime.datetime.today().strftime("%Y-%m-%d"),
            day_quantity=0,
            night_quantity=0,
            )
            obj.save()

        description = production_amount.values('production_date').distinct()
    production_date_raw = []
    for i in description:
        if i['production_date'] != None:
            date_object = datetime.datetime.strptime(str(i['production_date']), '%Y-%m-%d')
            formatted_date_new = date_object.strftime('%d-%m-%Y')
            production_date_raw.append(str(formatted_date_new))
    production_date = sorted(str(datetime.datetime.strptime(x, '%d-%m-%Y').strftime('%Y-%m-%d')) for x in production_date_raw)

    production_test = []
    for j in data_id:
        if ProductionDelivery.objects.filter(articles=j):
            production_test.append(ProductionDelivery.objects.filter(articles=j)[0])

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
            if data.filter(Q(task=task,), Q(subject=subject_list[i])):
                data.filter(supplier_article=supplier_article_list[i]).update(
                from_stock=from_stock_list[i],
                amount=amount_list[i],
                )
            else:
                obj = ArticlesDelivery(
                task=task,
                subject=subject_list[i],
                supplier_article=supplier_article_list[i],
                from_stock=from_stock_list[i],
                amount=amount_list[i],
                )
                obj.save()
        return redirect(f'delivery_data', task_id)
    elif request.method == 'POST':
        #article_id = ArticlesDelivery.objects.get(id=list(request.POST.keys())[3])
        article_id = list(request.POST.keys())[3]
        date_for_production = list(request.POST.keys())[1][:10]
        date_object = datetime.datetime.strptime(date_for_production, '%Y-%m-%d')
        formatted_date = date_object.strftime('%Y-%m-%d')
        article = list(request.POST.keys())[1]
        
        for_data = article.split(", ")
        for_data_id = data.get(supplier_article=for_data[2])
        if production_amount.filter(Q(id=article_id)):
            production_amount.filter(id=article_id).update(
            day_quantity=list(request.POST.values())[1],
            night_quantity=list(request.POST.values())[2],
            )
            
        else:
            obj = ProductionDelivery(
            task=task,
            id=article_id,
            articles = for_data_id,
            production_date=formatted_date,
            day_quantity=list(request.POST.values())[1],
            night_quantity=list(request.POST.values())[2],
            )
            obj.save()

        return redirect(f'delivery_data', task_id)

    context = {
        'task':task,
        'data': data,
        'production_test':production_test,
        'production_date': production_date,
        'today': today,
        'production_amount': production_amount
    }
    return render(request, 'production/delivery_data.html', context)
