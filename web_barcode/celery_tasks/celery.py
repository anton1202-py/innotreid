from celery import Celery
from celery.schedules import crontab


app = Celery('celery_tasks',
             include=['celery_tasks.tasks', 'celery_tasks.tasks_yandex_fby_fbs'])
app.config_from_object('celery_tasks.celeryconfig')


app.conf.beat_schedule = {
    "everyday-task": {
        "task": "celery_tasks.tasks.add_database_data",
        "schedule": crontab(hour=22, minute=40)
    },
    "everyday-task": {
        "task": "celery_tasks.tasks.add_stock_data_from_frontend",
        "schedule": crontab(hour=7, minute=0)
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
}

