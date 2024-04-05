import datetime
import logging
import os

from celery import Celery
from celery.schedules import crontab, schedule

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web_barcode.settings")

app = Celery('celery_tasks',
             include=['celery_tasks.google_sheet_tasks',
                      'celery_tasks.ozon_tasks',
                      'celery_tasks.tasks',
                      'celery_tasks.tasks_yandex_fby_fbs',
                      'celery_tasks.yandex_tasks',
                      'ozon_system.tasks',
                      'fbs_mode.tasks',
                      'price_system.periodical_tasks',
                      'reklama.periodic_tasks',
                      ])
app.config_from_object('celery_tasks.celeryconfig')

# настройка логирования
logging.basicConfig(filename='celery_tasks/celery.log', level=logging.INFO,
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
    "ozon_system_del_articles_low_price": {
        "task": "ozon_system.tasks.delete_ozon_articles_with_low_price_from_actions",
        'schedule': crontab(hour='6,18', minute=0),
    },
    "ooo_fbs_action": {
        "task": "fbs_mode.tasks.ooo_common_task",
        "schedule": crontab(hour=17, minute=40)
    },
    "ip_fbs_morning_action": {
        "task": "fbs_mode.tasks.ip_morning_task",
        "schedule": crontab(hour=5, minute=40)
    },
    "ip_ozon_day": {
        "task": "fbs_mode.tasks.ip_ozon_action_day",
        "schedule": crontab(hour=8, minute=10)
    },
    "ip_fbs_friday_action": {
        "task": "fbs_mode.tasks.ip_friday_task",
        "schedule": crontab(hour=17, minute=20, day_of_week=5)
    },
    "google_sheet_task": {
        "task": "celery_tasks.google_sheet_tasks.google_sheet",
        "schedule": crontab(hour=18, minute=0, day_of_week=1)
    },
    "ozon_balance_task": {
        "task": "celery_tasks.ozon_tasks.fbs_balance_maker_for_all_company",
        "schedule": crontab(hour=5, minute=0)
    },
    "yandex_balance_task": {
        "task": "celery_tasks.yandex_tasks.fbs_balance_updater",
        "schedule": crontab(hour=5, minute=5)
    },

    "price_system_wb_task": {
        "task": "price_system.periodical_tasks.common_wb_add_price_info",
        "schedule": crontab(hour=7, minute=16)
    },
    "price_system_ozon_task": {
        "task": "price_system.periodical_tasks.common_ozon_add_price_info",
        "schedule": crontab(hour=7, minute=17)
    },
    "price_system_yandex_task": {
        "task": "price_system.periodical_tasks.common_yandex_add_price_info",
        "schedule": crontab(hour=7, minute=18)
    },
    "price_system_compare_ooo_articles": {
        "task": "price_system.periodical_tasks.periodic_compare_ooo_articles",
        "schedule": crontab(hour=5, minute=0, day_of_week=1)
    },
    "price_system_compare_ip_articles": {
        "task": "price_system.periodical_tasks.periodic_compare_ip_articles",
        "schedule": crontab(hour=5, minute=10, day_of_week=1)
    },

    "wb_reklama_campaign_budget_add": {
        "task": "reklama.periodic_tasks.budget_working",
        "schedule": crontab(hour=21, minute=1)
    },
    "wb_ooo_article_add_to_db": {
        "task": "reklama.periodic_tasks.ooo_wb_articles_data",
        "schedule": crontab(hour=22, minute=0)
    },
    "wb_ooo_matching_article_campaign": {
        "task": "reklama.periodic_tasks.matching_wb_ooo_article_campaign",
        "schedule": crontab(hour=9, minute=10)
    },
    "wb_ooo_stock_fbo": {
        "task": "reklama.periodic_tasks.wb_ooo_fbo_stock_count",
        "schedule": crontab(hour=22, minute=20)
    },

    "ozon_reklama_stop_start_campaign": {
        "task": "reklama.periodic_tasks.ozon_start_stop_nessessary_campaign",
        "schedule": crontab(hour=21, minute=0)
    },
}
