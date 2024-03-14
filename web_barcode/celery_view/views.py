import importlib
import inspect
from datetime import date, datetime, timedelta

from celery import current_app
from celery.schedules import crontab
from celery_tasks.celery import app as celery_app
from django.shortcuts import get_object_or_404, redirect, render


def doc_type(function_path):
    module_name, function_name = function_path.rsplit('.', 1)
    # Динамически импортируем модуль
    module = importlib.import_module(module_name)

    # Получаем объект функции
    function = getattr(module, function_name)

    # Получаем документацию функции
    docstring = inspect.getdoc(function)

    return docstring


def wb_articles_list():
    """Получаем массив арткулов с ценами и скидками для ВБ"""
    n = 1 + '23'
    print(n)


def celery_tasks_view(request):
    """Показывает задачи celery на странице"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')

    tasks_info = []
    print(doc_type('celery_tasks.ozon_tasks.fbs_balance_maker_for_all_company'))
    for task_name, task_config in celery_app.conf.beat_schedule.items():
        inner_list = []
        inner_list.append(task_config['task'])

        if task_config['task'] in celery_app.tasks:
            inner_list.append(celery_app.tasks[task_config['task']].__doc__)
        else:
            inner_list.append('doc_type(task_config["task"])')

        next_run_time = task_config['schedule']
        hour = list(next_run_time.hour)[0] + 3
        if hour >= 24:
            hour = hour - 24
        minute = list(next_run_time.minute)[0]

        # Форматируем время в нужный формат
        time_str = f"{hour:02d}:{minute:02d}:00"
        if len(next_run_time.minute) > 1:
            time_str = f'*/{list(sorted(next_run_time.minute))[1]}'
        inner_list.append(time_str)
        tasks_info.append(inner_list)

    context = {
        'data': tasks_info,
    }

    return render(request, 'celery_view/celery_tasks.html', context)
