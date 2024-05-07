import importlib
import inspect
from datetime import date, datetime, timedelta

from celery import current_app
from celery.schedules import crontab
from celery_tasks.celery import app as celery_app
from celery_tasks.file_for_create import get_current_ssp
from celery_tasks.google_sheet_tasks import wb_data
from django.http import HttpResponse
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


def celery_tasks_view(request):
    """Показывает задачи celery на странице"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    tasks_info = []
    for task_name, task_config in celery_app.conf.beat_schedule.items():
        inner_list = []
        inner_list.append(task_config['task'])

        if task_config['task'] in celery_app.tasks:
            inner_list.append(celery_app.tasks[task_config['task']].__doc__)
        else:
            inner_list.append(doc_type(task_config["task"]))

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

    return render(request, 'celery_view/celery_page.html', context)


def long_running_function_view(request):
    row_id = request.GET.get('row_id')
    print(f'Нажата кнопка для старта задачи {row_id}')
    scheduled_tasks = celery_app.conf.beat_schedule.items()
    for task, options in scheduled_tasks:
        # print(task, row_id)
        if options['task'] == row_id:
            print('**************************')
            print(task, options['task'], row_id)
            print('**************************')
            celery_app.send_task(task)
            print(celery_app.send_task(task))
            print('Функция должна отработать')
            return HttpResponse(f"Задача {row_id} запущена")

    return HttpResponse(f"Задача {row_id} не найдена в расписании")
