import datetime
import logging
import os

from celery import Celery
from celery.schedules import crontab, schedule

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web_barcode.settings")

app = Celery('celery_tasks',
             include=['celery_tasks.tasks',
                      'celery_tasks.google_sheet_tasks',
                      'celery_tasks.ozon_tasks',
                      'celery_tasks.yandex_tasks',
                      'ozon_system.tasks',
                      'fbs_mode.tasks',
                      'price_system.periodical_tasks',
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
    "add_fby_amount": {
        "task": "celery_tasks.tasks_yandex_fby_fbs.add_fby_amount_to_database",
        "schedule": crontab(hour=6, minute=0)
    },
    "send_tg_message": {
        "task": "celery_tasks.tasks_yandex_fby_fbs.sender_zero_balance",
        "schedule": crontab(hour=7, minute=10)
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
    "wb_ip_action": {
        "task": "fbs_mode.tasks.ip_wb_action",
        "schedule": crontab(hour=5, minute=40)
    },
    "wb_ip_action_friday": {
        "task": "fbs_mode.tasks.ip_wb_action",
        "schedule": crontab(hour=17, minute=20, day_of_week=5)
    },
    "file_ip_action_friday": {
        "task": "fbs_mode.tasks.ip_production_file",
        "schedule": crontab(hour=17, minute=26, day_of_week=5)
    },
    "ozon_ip_morning": {
        "task": "fbs_mode.tasks.ip_ozon_action_morning",
        "schedule": crontab(hour=5, minute=48)
    },
    "yandex_ip_action": {
        "task": "fbs_mode.tasks.ip_yandex_action",
        "schedule": crontab(hour=5, minute=55)
    },
    "file_ip_action": {
        "task": "fbs_mode.tasks.ip_production_file",
        "schedule": crontab(hour=5, minute=58)
    },
    "ozon_ip_day": {
        "task": "fbs_mode.tasks.ip_ozon_action_day",
        "schedule": crontab(hour=8, minute=10)
    },

    "wb_ooo_action": {
        "task": "fbs_mode.tasks.ooo_wb_action",
        "schedule": crontab(hour=17, minute=40)
    },
    "ozon_ooo_action": {
        "task": "fbs_mode.tasks.ooo_ozon_action",
        "schedule": crontab(hour=17, minute=48)
    },
    "yandex_ooo_action": {
        "task": "fbs_mode.tasks.ooo_yandex_action",
        "schedule": crontab(hour=17, minute=55)
    },
    "file_ooo_action": {
        "task": "fbs_mode.tasks.ooo_production_file",
        "schedule": crontab(hour=17, minute=58)
    },
    "google_sheet_task": {
        "task": "celery_tasks.google_sheet_tasks.google_sheet",
        "schedule": crontab(hour=18, minute=0, day_of_week=1)
    },
    "ozon_balance_task": {
        "task": "celery_tasks.ozon_tasks.fbs_balance_maker",
        "schedule": crontab(hour=5, minute=0)
    },
    "yandex_balance_task": {
        "task": "celery_tasks.yandex_tasks.fbs_balance_updater",
        "schedule": crontab(hour=5, minute=5)
    },
    "price_system_wb_task": {
        "task": "price_system.periodical_tasks.wb_articles_list",
        "schedule": crontab(hour=18, minute=19)
    },
}
