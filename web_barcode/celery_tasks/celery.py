import logging

from celery import Celery
from celery.schedules import crontab

app = Celery('celery_tasks',
             include=['celery_tasks.tasks', 'ozon_system.tasks', 'celery_tasks.tasks_yandex_fby_fbs'])
app.config_from_object('celery_tasks.celeryconfig')

# настройка логирования
logging.basicConfig(filename='celery.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

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
}
