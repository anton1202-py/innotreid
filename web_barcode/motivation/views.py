import ast
import json
import os
from datetime import datetime

from django.contrib.auth.models import Group
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.generic import DetailView, ListView
from motivation.google_sheet_report import (
    article_data_for_sheet, article_last_month_sales_google_sheet,
    designer_google_sheet, sale_article_per_month)
from motivation.models import Selling
from motivation.supplyment import (
    get_article_draw_authors_sales_data, get_draw_authors_year_monthly_reward,
    import_sales_2023, motivation_article_type_excel_file_export,
    motivation_article_type_excel_import,
    motivation_designer_rewards_excel_file_export)
from price_system.models import Articles, DesignUser
from users.models import InnotreidUser


def get_main_sales_data(year):
    """Отдает данные по продажам артикулов"""

    sale_data = Selling.objects.filter(year=year).values(
        'lighter', 'month', 'quantity', 'summ')
    # Словарь с данными артикула по продажам по месяцам
    main_sales_dict = {}
    # Словарь с продажами артикула за текущий год
    year_sales_dict = {}
    for data in sale_data:
        if data['lighter'] in main_sales_dict:
            if data['month'] in main_sales_dict[data['lighter']]:
                main_sales_dict[data['lighter']
                                ][data['month']] += int(data['quantity'])
            else:
                main_sales_dict[data['lighter']
                                ][data['month']] = int(data['quantity'])
        else:
            main_sales_dict[data['lighter']] = {
                data['month']: int(data['quantity'])}
        if data['lighter'] in year_sales_dict:
            year_sales_dict[data['lighter']] += int(data['quantity'])
        else:
            year_sales_dict[data['lighter']] = int(data['quantity'])
    return year_sales_dict, main_sales_dict


def get_amount_summ_sales_data(year):
    """Отдает данные по продажам артикулов"""
    sale_data = Selling.objects.filter(year=year).values(
        'lighter', 'month', 'quantity', 'summ')
    # Словарь с данными артикула по продажам по месяцам
    main_sales_dict = {}
    # Словарь с продажами артикула за текущий год
    year_sales_dict = {}
    for data in sale_data:
        if data['lighter'] in main_sales_dict:
            if data['month'] in main_sales_dict[data['lighter']]:
                main_sales_dict[data['lighter']
                                ][data['month']]['quantity'] += int(data['quantity'])
                main_sales_dict[data['lighter']
                                ][data['month']]['summ'] += int(data['summ'])
            else:
                main_sales_dict[data['lighter']
                                ][data['month']] = {'quantity': int(data['quantity']),
                                                    'summ': int(data['summ'])}
        else:
            main_sales_dict[data['lighter']] = {
                data['month']: {
                    'quantity': int(data['quantity']),
                    'summ': int(data['summ'])}}
        if data['lighter'] in year_sales_dict:
            year_sales_dict[data['lighter']
                            ]['quantity'] += int(data['quantity'])
            year_sales_dict[data['lighter']]['summ'] += int(data['summ'])
        else:
            year_sales_dict[data['lighter']] = {'quantity': int(data['quantity']),
                                                'summ': int(data['summ'])}
    return year_sales_dict, main_sales_dict


def get_designers_amount_summ_sales_data(innotreiduser, year):
    """Отдает данные по продажам артикулов"""
    sale_data = Selling.objects.filter(year=year).values(
        'lighter', 'month', 'quantity', 'summ', 'lighter__designer_article', 'lighter__copy_right', 'lighter__designer')
    designer_obj = DesignUser.objects.filter(designer=innotreiduser)[0]
    main_percent = designer_obj.main_reward_persent/100
    copyright_percent = designer_obj.copyright_reward_persent/100

    # Словарь с данными артикула по продажам по месяцам
    main_sales_dict = {}
    # Словарь с продажами артикула за текущий год
    year_sales_dict = {}
    for data in sale_data:
        percent = 0
        if data['lighter__copy_right'] == True:
            percent = copyright_percent
        else:
            percent = main_percent
        if data['lighter__designer'] == innotreiduser.id:
            if data['lighter'] in main_sales_dict:
                if data['month'] in main_sales_dict[data['lighter']]:
                    main_sales_dict[data['lighter']
                                    ][data['month']]['quantity'] += int(data['quantity'])
                    main_sales_dict[data['lighter']
                                    ][data['month']]['summ'] += int(data['summ'])*percent

                else:
                    main_sales_dict[data['lighter']
                                    ][data['month']] = {'quantity': int(data['quantity']),
                                                        'summ': int(data['summ'])*percent}
            else:
                main_sales_dict[data['lighter']] = {
                    data['month']: {
                        'quantity': int(data['quantity']),
                        'summ': int(data['summ'])*percent}}

            if data['lighter'] in year_sales_dict:
                year_sales_dict[data['lighter']
                                ]['quantity'] += int(data['quantity'])
                year_sales_dict[data['lighter']
                                ]['summ'] += int(data['summ'])*percent
            else:
                year_sales_dict[data['lighter']] = {'quantity': int(data['quantity']),
                                                    'summ': int(data['summ'])*percent}
    return year_sales_dict, main_sales_dict


def get_designers_sales_data(year):
    """Отдает данные по продажам дизайнеров"""
    sale_data = Selling.objects.filter(year=year).values(
        'lighter', 'month', 'summ', 'lighter__designer', 'lighter__designer_article', 'lighter__copy_right')
    designer_rew_dict = {}
    designer_persent = DesignUser.objects.all().values(
        'designer', 'main_reward_persent', 'copyright_reward_persent')
    for i in designer_persent:
        if i['copyright_reward_persent']:
            designer_rew_dict[i['designer']
                              ] = i['copyright_reward_persent']/100
        elif not i['copyright_reward_persent'] and i['main_reward_persent']:
            designer_rew_dict[i['designer']] = i['main_reward_persent']/100
        else:
            designer_rew_dict[i['designer']] = 0
    # Словарь с данными артикула по продажам по месяцам
    monthly_sales_dict = {}
    # Словарь с продажами артикула за текущий год
    year_sales_dict = {}
    for data in sale_data:

        if data['lighter__designer']:
            designer_obj = DesignUser.objects.filter(
                designer__id=data['lighter__designer'])[0]
            main_percent = designer_obj.main_reward_persent/100
            if designer_obj.copyright_reward_persent:
                copyright_percent = designer_obj.copyright_reward_persent/100
            percent = 0
            if data['lighter__copy_right'] == True:
                percent = copyright_percent
            else:
                percent = main_percent

            if data['lighter__designer'] in monthly_sales_dict:
                if data['month'] in monthly_sales_dict[data['lighter__designer']]:
                    monthly_sales_dict[data['lighter__designer']
                                       ][data['month']] += int(data['summ'])*percent
                else:
                    monthly_sales_dict[data['lighter__designer']
                                       ][data['month']] = int(data['summ'])*percent
            else:
                monthly_sales_dict[data['lighter__designer']] = {
                    data['month']: int(data['summ'])*percent}
            if data['lighter__designer'] in year_sales_dict:
                year_sales_dict[data['lighter__designer']
                                ] += int(data['summ'])*percent
            else:
                year_sales_dict[data['lighter__designer']] = int(
                    data['summ'])*percent
    return year_sales_dict, monthly_sales_dict


def get_article_sales_data(year):
    """Отдает данные по продажам артикулов"""
    sale_data = Selling.objects.filter(year=year).values(
        'lighter', 'month', 'summ', 'lighter__designer')
    # Словарь с продажами артикула за текущий год
    year_sales_dict = {}
    for data in sale_data:
        if data['lighter__designer']:

            if data['lighter__designer'] in year_sales_dict:
                year_sales_dict[data['lighter__designer']
                                ] += int(data['summ'])
            else:
                year_sales_dict[data['lighter__designer']] = int(
                    data['summ'])
    return year_sales_dict


def article_designers(request):
    """Отображает артикулы дизайнеров"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    # get_current_selling()
    current_year = datetime.now().strftime('%Y')
    page_name = 'Светильники дизайнеров'
    article_list = Articles.objects.filter(
        designer_article=True).order_by('common_article')

    # Проверяю наличия данных из формы фильтра юр лица.
    months = Selling.objects.filter(
        year=current_year).values('month').distinct()

    year_sales_dict, main_sales_dict = get_main_sales_data(current_year)

    # Получаем список пользователей из группы "Дизайнеры"
    designer_group = Group.objects.get(name='Дизайнеры')
    designer_list = designer_group.user_set.all()
    year_filter = Selling.objects.all().values('year').distinct()
    year_list = [int(value['year']) for value in year_filter]
    sales_year = current_year
    if request.POST:
        filter_company = request.POST.get('filter_data')
        common_article = request.POST.get("common_article")
        designer = request.POST.get("designer")
        select_year = request.POST.get("year_select")
        # if filter_company:
        #     article_list = Articles.objects.filter(
        #         company=filter_company).order_by('common_article')
        # request.session['filter_data'] = request.POST.get('filter_data')
        if common_article:
            article_list = Articles.objects.filter(
                Q(common_article=common_article)).order_by('common_article')
            # request.session['common_article'] = request.POST.get(
            #     'common_article')
        if designer:
            article_list = Articles.objects.filter(
                Q(designer=designer)).order_by('common_article')
            # request.session['designer'] = request.POST.get('designer')
        if select_year:
            months = Selling.objects.filter(
                year=select_year).values('month').distinct()
            year_sales_dict, main_sales_dict = get_main_sales_data(select_year)
            sales_year = select_year

        # return redirect('motivation_article_designers')
    month_list = [int(value['month']) for value in months]
    context = {
        'page_name': page_name,
        'article_list': article_list,
        'year_sales_dict': year_sales_dict,
        'year_list': year_list,
        'designer_list': designer_list,
        'month_list': sorted(month_list),
        'main_sales_dict': main_sales_dict,
        'sales_year': sales_year
    }
    return render(request, 'motivation/article_designers.html', context)


def update_model_field(request):
    if request.method == 'POST':
        # Сохраняем значение в базу данных
        user_id = request.POST.get('selected_designer')
        article = request.POST.get('article')
        if user_id:
            user_obj = InnotreidUser.objects.get(id=int(user_id))
            Articles.objects.filter(common_article=article).update(
                designer=user_obj)
        else:
            Articles.objects.filter(common_article=article).update(
                designer=None)
        return JsonResponse({'message': 'Value saved successfully.'})
    return JsonResponse({'error': 'Invalid request method.'}, status=400)


def filter_get_request(request, ur_lico):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        search_term = request.GET.get('search_term', None)
        article_list = Articles.objects.filter(
            common_article__contains=search_term)
        if search_term:
            filtered_articles = Articles.objects.filter(company=ur_lico,
                                                        common_article__contains=search_term).order_by('common_article')
        else:
            filtered_articles = Articles.objects.filter(
                company=ur_lico).order_by('common_article')
        data = [{'common_article': article.common_article,
                'designer_article': article.designer_article,
                 'copy_right': article.copy_right} for article in filtered_articles]
        return JsonResponse(data, safe=False)


def filter_get_delete_request(request):
    """Показывает таблицу при удалении артикулов из строки фильтра"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        search_term = request.GET.get('search_term', None)
        if search_term:
            filtered_articles = Articles.objects.filter(
                common_article__contains=search_term)
            data = [{'common_article': article.common_article,
                     'designer_article': article.designer_article,
                     'copy_right': article.copy_right} for article in filtered_articles]
        else:
            filtered_articles = Articles.objects.all()
            data = [{'common_article': article.common_article,
                     'designer_article': article.designer_article,
                     'copy_right': article.copy_right} for article in filtered_articles]
        return JsonResponse(data, safe=False)


def article_type(request):
    """
    Отображает тип светильника:
    дизайнерский или нет, с правами собственности или нет.
    """
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = 'Тип светильника'
    ur_lico = 'ООО Иннотрейд'
    if 'filter_data' in request.session:
        ur_lico = request.session['filter_data']
    article_list = Articles.objects.filter(company=ur_lico).order_by('common_article').values(
        'common_article', 'name', 'company', 'designer_article', 'copy_right')
    import_data = ''
    if request.GET:
        return filter_get_request(request, ur_lico)

    if request.POST:
        filter_company = request.POST.get('filter_data')
        if filter_company:
            article_list = Articles.objects.filter(
                company=filter_company).order_by('common_article').values(
                'common_article', 'name', 'company', 'designer_article', 'copy_right')
            request.session['filter_data'] = request.POST.get('filter_data')
        if 'export' in request.POST or 'import_file' in request.FILES:
            if request.POST.get('export') == 'create_file':
                return motivation_article_type_excel_file_export(article_list)

            elif 'import_file' in request.FILES:
                import_data = motivation_article_type_excel_import(
                    request.FILES['import_file'], ur_lico)
                if type(import_data) != str:
                    return redirect('motivation_article_type')
        if 'common_article' in request.POST:
            filter_data = request.POST
            article_filter = filter_data.get("common_article")
            article_list = Articles.objects.filter(company=ur_lico, common_article__contains=article_filter).order_by('common_article').values(
                'common_article', 'name', 'company', 'designer_article', 'copy_right')
    context = {
        'page_name': page_name,
        'article_list': article_list,
        'import_data': import_data
    }
    return render(request, 'motivation/article_type.html', context)


def update_article_designer_boolean_field(request):
    if request.method == 'POST':
        # Сохраняем значение в базу данных
        if 'designer_article_type' in request.POST:
            article_type = request.POST.get('designer_article_type')
            article = request.POST.get('article')
            checkbox_value = not ast.literal_eval(article_type)
            Articles.objects.filter(common_article=article).update(
                designer_article=checkbox_value)
            if article_type == 'None':
                Articles.objects.filter(common_article=article).update(
                    designer_article=True)
            elif article_type == 'True':
                Articles.objects.filter(common_article=article).update(
                    designer_article=None)
        elif 'non_designer_article_type' in request.POST:
            article_type = request.POST.get('non_designer_article_type')
            article = request.POST.get('article')
            if article_type == 'False':
                Articles.objects.filter(common_article=article).update(
                    designer_article=None)
            elif article_type == 'None':
                Articles.objects.filter(common_article=article).update(
                    designer_article=False)
        elif 'copyright_article_type' in request.POST:
            copyright_type = request.POST.get('copyright_article_type')
            article = request.POST.get('article')
            checkbox_value = not ast.literal_eval(copyright_type)
            Articles.objects.filter(common_article=article).update(
                copy_right=checkbox_value)

        return JsonResponse({'message': 'Value saved successfully.'})
    return JsonResponse({'error': 'Invalid request method.'}, status=400)


def update_article_copyright_boolean_field(request):
    if request.method == 'POST':

        # Сохраняем значение в базу данных
        copyright_type = request.POST.get('copyright_article_type')
        article = request.POST.get('article')
        checkbox_value = not ast.literal_eval(copyright_type)
        Articles.objects.filter(common_article=article).update(
            copy_right=checkbox_value)

        return JsonResponse({'message': 'Value saved successfully.'})
    return JsonResponse({'error': 'Invalid request method.'}, status=400)


def designers_rewards(request):
    """Отображает страницы с вознаграждением дизайнеров"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = 'Вознаграждение дизайнеров'
    sales_year = datetime.now().strftime('%Y')
    year_filter = Selling.objects.all().values('year').distinct()
    year_list = [int(value['year']) for value in year_filter]
    # Список месяцев в текущем году
    months = Selling.objects.filter(
        year=sales_year).values('month').distinct()
    month_list = [int(value['month']) for value in months]

    designer_main_percent = DesignUser.objects.values(
        'designer__id', 'main_reward_persent', 'copyright_reward_persent')
    designer_percent = {}
    for data in designer_main_percent:
        if data['main_reward_persent']:
            if data['copyright_reward_persent']:
                designer_percent[data['designer__id']
                                 ] = data['copyright_reward_persent']/100
            else:
                designer_percent[data['designer__id']
                                 ] = data['main_reward_persent']/100

    year_sales_dict, monthly_sales_dict = get_draw_authors_year_monthly_reward(
        sales_year)
    # year_article_sales_dict = get_article_sales_data(sales_year)
    year_article_sales_dict = get_article_draw_authors_sales_data(sales_year)
    # Находим группу "Дизайнеры"
    designer_group = Group.objects.get(name='Дизайнеры')

    # Получаем список пользователей из группы "Дизайнер"
    designer_users = designer_group.user_set.all()

    if request.POST:
        select_year = request.POST.get("year_select")
        if select_year:
            sales_year = select_year
            year_sales_dict, monthly_sales_dict = get_draw_authors_year_monthly_reward(
                select_year)
            year_article_sales_dict = get_article_draw_authors_sales_data(
                sales_year)
            months = Selling.objects.filter(
                year=select_year).values('month').distinct()
    month_list = [int(value['month']) for value in months]
    context = {
        'page_name': page_name,
        'designer_users': designer_users,
        'year_list': year_list,
        'monthly_sales_dict': monthly_sales_dict,
        'designer_percent': designer_percent,
        'year_sales_dict': year_sales_dict,
        'month_list': sorted(month_list),
        'sales_year': sales_year,
        'year_article_sales_dict': year_article_sales_dict

    }
    return render(request, 'motivation/designers_reward.html', context)


class MotivationDesignersRewardDetailView(DetailView):
    model = InnotreidUser
    template_name = 'motivation/designers_reward_detail.html'

    def get_context_data(self, **kwargs):
        context = super(MotivationDesignersRewardDetailView,
                        self).get_context_data(**kwargs)
        user_data = InnotreidUser.objects.get(id=self.kwargs['pk'])
        sales_year = datetime.now().strftime('%Y')
        months = Selling.objects.filter(
            year=sales_year).values('month').distinct()
        article_list = Articles.objects.filter(
            designer=self.kwargs['pk']).values()
        month_list = [int(value['month']) for value in months]
        year_sales_dict, main_sales_dict = get_designers_amount_summ_sales_data(
            user_data, sales_year)
        designer_id = int(self.kwargs['pk'])
        year_common_sales_dict, monthly_sales_dict = get_designers_sales_data(
            sales_year)
        year_reward = round(year_common_sales_dict[self.kwargs['pk']])
        year_filter = Selling.objects.all().values('year').distinct()
        year_list = [int(value['year']) for value in year_filter]
        context.update({
            'article_list': article_list,
            'page_name': f"Вознаграждение дизайнера {user_data.last_name} {user_data.first_name}",
            'month_list': sorted(month_list),
            'sales_year': sales_year,
            'year_list': year_list,
            'year_sales_dict': year_sales_dict,
            'main_sales_dict': main_sales_dict,
            'designer_id': designer_id,
            'year_reward': year_reward,
        })
        return context

    def post(self, request, *args, **kwargs):
        sales_year = datetime.now().strftime('%Y')
        months = Selling.objects.filter(
            year=sales_year).values('month').distinct()
        article_list = Articles.objects.filter(
            designer=self.kwargs['pk']).values()
        user_data = InnotreidUser.objects.get(id=self.kwargs['pk'])
        year_filter = Selling.objects.all().values('year').distinct()
        year_list = [int(value['year']) for value in year_filter]
        year_common_sales_dict, monthly_sales_dict = get_designers_sales_data(
            sales_year)
        year_sales_dict, main_sales_dict = get_designers_amount_summ_sales_data(
            user_data, sales_year)

        if request.POST:
            select_year = request.POST.get("year_select")

            if select_year:
                months = Selling.objects.filter(
                    year=select_year).values('month').distinct()
                sales_year = select_year
                year_sales_dict, main_sales_dict = get_designers_amount_summ_sales_data(
                    user_data, sales_year)
                year_common_sales_dict, monthly_sales_dict = get_designers_sales_data(
                    sales_year)
            if 'export' in request.POST:
                month_list = [int(value['month']) for value in months]
                month_list.sort()
                return motivation_designer_rewards_excel_file_export(article_list,
                                                                     year_sales_dict, main_sales_dict, f'{user_data.last_name} {user_data.first_name}', sales_year, month_list)

        designer_id = int(self.kwargs['pk'])

        user_data = InnotreidUser.objects.get(id=self.kwargs['pk'])
        # context = self.get_context_data()
        month_list = [int(value['month']) for value in months]
        year_reward = round(year_common_sales_dict[self.kwargs['pk']])
        context = {
            'article_list': article_list,
            'page_name': f"Вознаграждение дизайнера {user_data.last_name} {user_data.first_name}",
            'month_list': sorted(month_list),
            'sales_year': sales_year,
            'year_list': year_list,
            'year_sales_dict': year_sales_dict,
            'main_sales_dict': main_sales_dict,
            'designer_id': designer_id,
            'year_reward': year_reward,
        }
        return self.render_to_response(context)


def download_designer_rewards_excel(request):

    year_sales_dict = ast.literal_eval(request.POST.get('year_sales_dict'))
    article_list = request.POST.get('article_list')
    cleaned_string = article_list.strip("<QuerySet").strip(">")

    article_list = ast.literal_eval(cleaned_string)
    main_sales_dict = ast.literal_eval(request.POST.get('main_sales_dict'))
    designer_id = int(request.POST.get('designer_id'))
    sales_year = int(request.POST.get('sales_year'))
    month_list = ast.literal_eval(request.POST.get('month_list'))
    user_data = InnotreidUser.objects.get(id=designer_id)
    print(article_list)
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{user_data.last_name}_{user_data.first_name}_rewards.xlsx"'
    motivation_designer_rewards_excel_file_export(
        article_list, year_sales_dict, main_sales_dict, f'{user_data.last_name} {user_data.first_name}', sales_year, month_list, response)

    return response


class MotivationDesignersSaleDetailView(DetailView):
    model = InnotreidUser
    template_name = 'motivation/designers_sale_detail.html'

    def get_context_data(self, **kwargs):
        context = super(MotivationDesignersSaleDetailView,
                        self).get_context_data(**kwargs)
        user_data = InnotreidUser.objects.get(id=self.kwargs['pk'])
        sales_year = datetime.now().strftime('%Y')
        designer_id = int(self.kwargs['pk'])
        months = Selling.objects.filter(
            year=sales_year).values('month').distinct()
        month_list = [int(value['month']) for value in months]
        year_sales_dict, main_sales_dict = get_amount_summ_sales_data(
            sales_year)

        year_article_sales_dict = get_article_sales_data(sales_year)
        year_sales = round(year_article_sales_dict[self.kwargs['pk']])
        year_filter = Selling.objects.all().values('year').distinct()
        year_list = [int(value['year']) for value in year_filter]
        context.update({
            'article_list': Articles.objects.filter(
                designer=self.kwargs['pk']).values(),
            'page_name': f"Продажи артикулов дизайнера {user_data.last_name} {user_data.first_name}",
            'month_list': sorted(month_list),
            'sales_year': sales_year,
            'year_list': year_list,
            'year_sales_dict': year_sales_dict,
            'main_sales_dict': main_sales_dict,
            'designer_id': designer_id,
            'year_sales': year_sales,

        })
        return context

    def post(self, request, *args, **kwargs):
        sales_year = datetime.now().strftime('%Y')
        months = Selling.objects.filter(
            year=sales_year).values('month').distinct()
        year_filter = Selling.objects.all().values('year').distinct()
        year_list = [int(value['year']) for value in year_filter]
        user_data = InnotreidUser.objects.get(id=self.kwargs['pk'])
        year_article_sales_dict = get_article_sales_data(sales_year)
        designer_id = int(self.kwargs['pk'])
        if request.POST:
            select_year = request.POST.get("year_select")
            user_data = InnotreidUser.objects.get(id=self.kwargs['pk'])
            if select_year:
                months = Selling.objects.filter(
                    year=select_year).values('month').distinct()
                sales_year = select_year
                year_sales_dict, main_sales_dict = get_amount_summ_sales_data(
                    sales_year)
                year_article_sales_dict = get_article_sales_data(sales_year)

        # context = self.get_context_data()
        month_list = [int(value['month']) for value in months]
        year_sales = round(year_article_sales_dict[self.kwargs['pk']])
        context = {
            'article_list': Articles.objects.filter(
                designer=self.kwargs['pk']).values(),
            'page_name': f"Вознаграждение дизайнера {user_data.last_name} {user_data.first_name}",
            'month_list': sorted(month_list),
            'sales_year': sales_year,
            'year_list': year_list,
            'year_sales_dict': year_sales_dict,
            'main_sales_dict': main_sales_dict,
            'designer_id': designer_id,
            'year_sales': year_sales,
        }
        return self.render_to_response(context)

    # def get_queryset(self):
    #     return Selling.objects.filter(
    #         lighter__designer=self.kwargs['designer'])


def percent_designers_rewards(request):
    """Отображает страницу с процентами награждения каждого дизайнера"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = 'Процент вознаграждения'
    percent_data = DesignUser.objects.all().order_by('designer__last_name')
    context = {
        'page_name': page_name,
        'percent_data': percent_data
    }
    return render(request, 'motivation/percent_reward.html', context)


def update_percent_reward(request):
    if request.method == 'POST':
        designer = request.POST.get('designer')
        # Сохраняем значение % за авторство в базу данных
        if 'main_percent' in request.POST:
            main_persent = request.POST.get('main_percent')
            DesignUser.objects.filter(designer__username=designer).update(
                main_reward_persent=main_persent
            )
        # Сохраняем значение % за интелектуальное право в базу данных
        if 'copyright_percent' in request.POST:
            copyright_persent = request.POST.get('copyright_percent')
            DesignUser.objects.filter(designer__username=designer).update(
                copyright_reward_persent=copyright_persent
            )
        return JsonResponse({'message': 'Value saved successfully.'})
    return JsonResponse({'error': 'Invalid request method.'}, status=400)
