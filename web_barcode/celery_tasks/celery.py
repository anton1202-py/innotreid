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
                      'analytika_reklama.periodic_tasks',
                      'create_reklama.periodic_tasks',
                      'database.periodic_tasks',
                      'feedbacks.periodic_tasks',
                      'ozon_system.tasks',
                      'motivation.google_sheet_report',
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
    "database_wb_sales_every_day": {
        "task": "database.periodic_tasks.process_wb_sales_data",
        "schedule": crontab(hour=7, minute=20)
    },
    "database_ozon_orders_every_day": {
        "task": "database.periodic_tasks.process_ozon_daily_orders",
        "schedule": crontab(hour=7, minute=15)
    },
    "database_yandex_orders_every_day": {
        "task": "database.periodic_tasks.process_yandex_daily_orders",
        "schedule": crontab(hour=7, minute=10)
    },
    "database_ozon_sales_every_month": {
        "task": "database.periodic_tasks.process_ozon_sales_data",
        "schedule": crontab(0, 0, day_of_month='10')
    },

    "add_fby_amount": {
        "task": "celery_tasks.tasks_yandex_fby_fbs.add_fby_amount_to_database",
        "schedule": crontab(hour=6, minute=0)
    },
    "send_tg_message": {
        "task": "celery_tasks.tasks_yandex_fby_fbs.sender_zero_balance",
        "schedule": crontab(hour=7, minute=10)
    },

    # =========== ЗАДАЧИ РАЗДЕЛА ANALYTIKA_REKLAMA ========== #
    "analytika_reklama_adv_common_statistic": {
        "task": "analytika_reklama.periodic_tasks.add_campaigns_statistic_to_db",
        "schedule": crontab(hour=18, minute=23)
    },
    "analytika_reklama_cluster_statistic_auto_adv": {
        "task": "analytika_reklama.periodic_tasks.get_clusters_statistic_for_autocampaign",
        "schedule": crontab(hour=18, minute=25)
    },
    "analytika_reklama_keywords_statistic_search_catalog_adv": {
        "task": "analytika_reklama.periodic_tasks.get_searchcampaign_keywords_statistic",
        "schedule": crontab(hour=18, minute=27)
    },
    "analytika_reklama_keywords_articles": {
        "task": "analytika_reklama.periodic_tasks.keyword_for_articles",
        "schedule": crontab(hour=18, minute=29)
    },
    "analytika_reklama_articles_excluded": {
        "task": "analytika_reklama.periodic_tasks.articles_excluded",
        "schedule": crontab(hour=18, minute=31)
    },
    # =========== КОНЕЦ РАЗДЕЛА ANALYTIKA_REKLAMA ========== #

    # =========== ЗАДАЧИ РАЗДЕЛА CREATE_REKLAMA ========== #
    "create_reklama_search_catalog_excluded": {
        "task": "create_reklama.periodic_tasks.set_up_minus_phrase_to_search_catalog_campaigns",
        "schedule": crontab(hour=1, minute=0)
    },
    "create_reklama_auto_excluded": {
        "task": "create_reklama.periodic_tasks.set_up_minus_phrase_to_auto_campaigns",
        "schedule": crontab(hour=1, minute=1)
    },
    "create_reklama_update_price": {
        "task": "create_reklama.periodic_tasks.update_articles_price_info_in_campaigns",
        "schedule": crontab(hour=1, minute=2)
    },
    "create_reklama_update_status": {
        "task": "create_reklama.periodic_tasks.update_campaign_status",
        "schedule": crontab(hour=2, minute=2)
    },
    "create_reklama_update_balance_and_cpm": {
        "task": "create_reklama.periodic_tasks.update_campaign_budget_and_cpm",
        "schedule": crontab(minute='*/180')
    },
    "create_reklama_add_balance": {
        "task": "create_reklama.periodic_tasks.budget_working",
        "schedule": crontab(hour=21, minute=1)
    },

    "create_reklama_wb_ooo_matching_article_campaign": {
        "task": "create_reklama.periodic_tasks.matching_wb_ooo_article_campaign",
        "schedule": crontab(hour=22, minute=10)
    },
    "create_reklama_ozon_ooo_matching_article_campaign": {
        "task": "create_reklama.periodic_tasks.matching_ozon_ooo_article_campaign",
        "schedule": crontab(hour=22, minute=15)
    },
    "create_reklama_wb_ooo_stock_fbo": {
        "task": "create_reklama.periodic_tasks.wb_ooo_fbo_stock_count",
        "schedule": crontab(hour=22, minute=20)
    },
    # =========== КОНЕЦ РАЗДЕЛА CREATE_REKLAMA ========== #

    # =========== ЗАДАЧИ РАЗДЕЛА FEEDBACKS (ОТЗЫВЫ) ========== #
    "feedbacks_for_articles": {
        "task": "feedbacks.periodic_tasks.get_feedback_for_nmid_from_wb",
        "schedule": crontab(hour=2, minute=0)
    },
    # =========== КОНЕЦ РАЗДЕЛА FEEDBACKS (ОТЗЫВЫ) ========== #

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

    # "ip_fbs_friday_action_test": {
    #     "task": "fbs_mode.tasks.ip_friday_task",
    #     "schedule": crontab(hour=7, minute=53)
    # },

    "google_sheet_task": {
        "task": "celery_tasks.google_sheet_tasks.google_sheet",
        "schedule": crontab(hour=19, minute=0, day_of_week=1)
    },

    # =========== ЗАДАЧИ РАЗДЕЛА МОТИВАЦИЯ ========== #
    "designer_google_sheet_articles": {
        "task": "motivation.google_sheet_report.get_data_designer_articles_to_google_sheet",
        "schedule": crontab(hour=2, minute=1)
    },
    # =========== КОНЕЦ РАЗДЕЛА МОТИВАЦИЯ ========== #

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
        "task": "price_system.periodical_tasks.periodic_compare_articles",
        "schedule": crontab(hour=5, minute=0)
    },
    "price_system_compare_ip_articles": {
        "task": "price_system.periodical_tasks.write_group_spp_data",
        "schedule": crontab(minute='*/40')
    },

}
