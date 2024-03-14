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


def celery_tasks_view(request):
    """Показывает задачи celery на странице"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    tasks = current_app.tasks
    now_date = datetime.now().strftime('%d-%m-%Y 00:00:00')
    tasks_info = []
    # print(celery_app.tasks)
    counter = 0
    counter_common = 0
    for task_name, task_config in celery_app.conf.beat_schedule.items():
        print(task_config['task'])
        # print(task_name, '           ', task_config)
        inner_dict = {}
        inner_list = []
        # print(task_config['task'])
        counter_common += 1
        inner_list.append(task_config['task'])

        # if task_config['task'] in celery_app.tasks:
        inner_list.append(doc_type(task_config['task']))
        #     counter += 1
        # else:
        #     inner_list.append('')

        # inner_dict['Описание'] = celery_app.tasks[task_config['task']].__doc__

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
