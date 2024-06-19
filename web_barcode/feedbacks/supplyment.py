import json

import pandas as pd
from api_request.wb_requests import average_rating_feedbacks_amount
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg
from reklama.models import UrLico

from web_barcode.constants_file import (CHAT_ID_ADMIN, CHAT_ID_EU,
                                        TELEGRAM_TOKEN, bot, header_ozon_dict,
                                        header_wb_data_dict, header_wb_dict,
                                        header_yandex_dict,
                                        ozon_adv_client_access_id_dict,
                                        ozon_adv_client_secret_dict,
                                        ozon_api_token_dict,
                                        wb_headers_karavaev, wb_headers_ooo,
                                        yandex_business_id_dict)

from .models import (FeedbacksWildberries, PhotoLinks, ProductDetails,
                     WildberriesAnswerFeedback)


@sender_error_to_tg
def get_wb_nmid_list() -> dict:
    """Функция получаеn список номенклатурных номер WB

    Возвращает словарь типа {юр_лицо: [список_nm_id]}
    """
    main_returned_data_dict = {}
    urlico_data = UrLico.objects.all()
    for ur_lico_obj in urlico_data:
        inner_article_list = []
        articles_data = Articles.objects.filter(
            company=ur_lico_obj.ur_lice_name,
            wb_nomenclature__isnull=False).values('wb_nomenclature')
        for article in articles_data:
            inner_article_list.append(article['wb_nomenclature'])
        main_returned_data_dict[ur_lico_obj] = inner_article_list

    return main_returned_data_dict


@sender_error_to_tg
def add_feedback_to_db(ur_lico_obj, nmid, nm_feedbacks):
    """Записывает отзывы артикула в базу данных."""
    article_obj = Articles.objects.filter(
        company=ur_lico_obj.ur_lice_name,
        wb_nomenclature=nmid)[0]
    if len(Articles.objects.filter(
            company=ur_lico_obj.ur_lice_name,
            wb_nomenclature=nmid)) > 1:
        print(Articles.objects.filter(
            company=ur_lico_obj.ur_lice_name,
            wb_nomenclature=nmid))

    for feedback in nm_feedbacks:
        if not FeedbacksWildberries.objects.filter(feedbackid=feedback['id']).exists():
            feedback_obj = FeedbacksWildberries(
                common_article=article_obj,
                ur_lico=ur_lico_obj,
                feedbackid=feedback['id'],
                user_name=feedback['userName'],
                text=feedback['text'],
                product_valuation=feedback['productValuation'],
                created_date=feedback['createdDate'],
                state=feedback['state'],
                was_viewed=feedback['wasViewed'],
                is_able_supplier_feedback_valuation=feedback['isAbleSupplierFeedbackValuation'],
                supplier_feedback_valuation=feedback['supplierFeedbackValuation'],
                is_able_supplier_product_valuation=feedback['isAbleSupplierProductValuation'],
                supplier_product_valuation=feedback['supplierProductValuation'],
                is_able_return_product_orders=feedback['isAbleReturnProductOrders'],
                return_product_orders_date=feedback['returnProductOrdersDate'],
                bables=feedback['bables']
            ).save()

            if feedback['answer']:
                WildberriesAnswerFeedback(
                    feedback=feedback_obj,
                    text=feedback['answer']['text'],
                    answer_state=feedback['answer']['state']
                ).save()

            ProductDetails(
                feedback=feedback_obj,
                nmid=feedback['productDetails']['nmId'],
                imtid=feedback['productDetails']['imtId'],
                product_name=feedback['productDetails']['productName'],
                supplier_article=feedback['productDetails']['supplierArticle'],
                supplier_name=feedback['productDetails']['supplierName'],
                brand_name=feedback['productDetails']['brandName'],
                size=feedback['productDetails']['size']
            ).save()

            if feedback['photoLinks']:
                for picture_data in feedback['photoLinks']:
                    PhotoLinks(
                        feedback=feedback_obj,
                        full_size=picture_data['fullSize'],
                        mini_size=picture_data['miniSize']
                    ).save()


def excel_import_previously_data(xlsx_file):
    """Импортирует данные о группе артикула из Excel"""

    excel_data_common = pd.read_excel(xlsx_file)
    column_list = excel_data_common.columns.tolist()
    if 'ID отзыва' in column_list and 'Номенклатура' in column_list and 'Текст отзыва' in column_list:
        excel_data = pd.DataFrame(excel_data_common, columns=[
                                  'ID отзыва',
                                  'Дата', 'Артикул',
                                  'Номенклатура',
                                  'Количество звезд',
                                  'Бренд',
                                  'Текст отзыва',
                                  'Имя'])
        id_feedback_list = excel_data['ID отзыва'].to_list()
        date_list = excel_data['Дата'].to_list()
        article_list = excel_data['Артикул'].to_list()
        nom_list = excel_data['Номенклатура'].to_list()
        stars_list = excel_data['Количество звезд'].to_list()
        brand_list = excel_data['Бренд'].to_list()
        text_list = excel_data['Текст отзыва'].to_list()
        name_list = excel_data['Имя'].to_list()

        # Словарь {артикул: название_группы}
        article_value_dict = {}
        # Список для обновления строк в БД
        new_objects = []
        error_group_name_list = []

        for i in range(len(nom_list)):
            if Articles.objects.filter(wb_nomenclature=nom_list[i]).exists():

                article_obj = Articles.objects.filter(
                    wb_nomenclature=nom_list[i])[0]
                ur_lico_obj = UrLico.objects.get(
                    ur_lice_name=article_obj.company)
                FeedbacksWildberries(
                    common_article=article_obj,
                    ur_lico=ur_lico_obj,
                    feedbackid=id_feedback_list[i],
                    user_name=name_list[i],
                    text=text_list[i],
                    product_valuation=stars_list[i],
                    created_date=date_list[i]
                ).save()
            else:
                print(
                    f'Артикул не нашел в базе {nom_list[i]}: {article_list[i]}')
