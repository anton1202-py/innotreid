import datetime
import logging
import os

from celery import Celery
from celery.schedules import crontab, schedule

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web_barcode.settings")

app = Celery('celery_tasks',
             include=['celery_tasks.tasks',
                      'ozon_system.tasks',
                      'fbs_mode.tasks',
                      'celery_tasks.tasks_yandex_fby_fbs'
                      ])
app.config_from_object('celery_tasks.celeryconfig')

# настройка логирования
logging.basicConfig(filename='celery.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

today = datetime.date.today()
if today.month < 12:
    first_day_of_next_month = datetime.date(today.year, today.month+1, 1)
elif today.month == 12:
    first_day_of_next_month = datetime.date(today.year+1, 1, 1)
penultimate_day_of_month = first_day_of_next_month - datetime.timedelta(days=2)

app.conf.beat_schedule = {
    "everyday-task1": {
        "task": "celery_tasks.tasks.add_database_data",
        "schedule": crontab(hour=7, minute=20)
    },
    "everyday-task": {
        "task": "celery_tasks.tasks.add_stock_data_from_frontend",
        "schedule": crontab(hour=7, minute=0)
    },
    "order_fbs_stat": {
        "task": "celery_tasks.tasks.orders_fbs_statistic",
        "schedule": crontab(hour=6, minute=30)
    },
    # "change-fbs": {
    #    "task": "celery_tasks.tasks_yandex_fby_fbs.change_fbs_amount",
    #   "schedule": crontab(hour=20, minute=40)
    # },
    "add_fby_amount": {
        "task": "celery_tasks.tasks_yandex_fby_fbs.add_fby_amount_to_database",
        "schedule": crontab(hour=6, minute=0)
    },
    "send_tg_message": {
        "task": "celery_tasks.tasks_yandex_fby_fbs.sender_zero_balance",
        "schedule": crontab(hour=10, minute=0)
    },
    "add_article_price_info_to_database": {
        "task": "celery_tasks.tasks.add_article_price_info_to_database",
        "schedule": crontab(hour=9, minute=0)
    },
    "sender_change_price_info": {
        "task": "celery_tasks.tasks.sender_change_price_info",
        "schedule": crontab(hour=9, minute=5)
    },
    "run-every-15-minutes": {
        "task": "celery_tasks.tasks.get_current_ssp",
        'schedule': crontab(minute='*/15'),
    },
    "stop-adv-all-ozon-company": {
        "task": "ozon_system.tasks.stop_adv_company",
        'schedule': crontab(day_of_month=30, hour=20, minute=0),
    },
    "start-adv-ozon-company": {
        "task": "ozon_system.tasks.start_adv_company",
        'schedule': crontab(day_of_month=penultimate_day_of_month.day, hour=20, minute=0),
    },
    "morning_wb_oz_action": {
        "task": "fbs_mode.tasks.common_action_wb_pivot_ozon_morning",
        "schedule": crontab(hour=10, minute=5)
    },
    "morning_only_oz_action": {
        "task": "fbs_mode.tasks.common_action_ozon_morning",
        "schedule": crontab(hour=11, minute=10)
    },
    "evening_wb_oz_action": {
        "task": "fbs_mode.tasks.common_action_evening",
        "schedule": crontab(hour=2, minute=0)
    },
}
