from api_request.wb_requests import average_rating_feedbacks_amount
from celery_tasks.celery import app
from feedbacks.supplyment import add_feedback_to_db, get_wb_nmid_list

from web_barcode.constants_file import header_wb_dict


@app.task
def get_feedback_for_nmid_from_wb():
    """Получает отзывы каждого артикула от API WB"""
    articles_data = get_wb_nmid_list()

    for ur_lico_obj, articles_list in articles_data.items():
        header = header_wb_dict[ur_lico_obj.ur_lice_name]

        for nmid in articles_list:
            nm_feedbacks = average_rating_feedbacks_amount(header, nmid)
            feedback_data = nm_feedbacks['data']['feedbacks']
            if feedback_data:
                add_feedback_to_db(ur_lico_obj, nmid, feedback_data)
