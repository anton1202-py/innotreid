from celery import Celery
from celery.schedules import crontab


app = Celery('celery_tasks',
             include=['celery_tasks.tasks'])
app.config_from_object('celery_tasks.celeryconfig')


app.conf.beat_schedule = {
    "everyday-task": {
        "task": "celery_tasks.tasks.add_database_data",
        "schedule": crontab(hour=13, minute=0)
    }
}

