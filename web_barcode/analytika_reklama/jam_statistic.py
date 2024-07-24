import re
from datetime import datetime

import pandas as pd
from analytika_reklama.models import (ArticleCampaignWhiteList,
                                      JamMainArticleKeyWords)
from analytika_reklama.phrase_statistic import add_keyphrase_to_db
from api_request.wb_requests import (advertisment_campaign_list,
                                     advertisment_campaigns_list_info,
                                     create_auto_advertisment_campaign,
                                     get_budget_adv_campaign)
from create_reklama.models import (AutoReplenish, CpmWbCampaign,
                                   CreatedCampaign, ProcentForAd)
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Side
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg
from reklama.models import UrLico

from web_barcode.constants_file import CHAT_ID_ADMIN, bot, header_wb_dict


# @sender_error_to_tg
def analytika_reklama_excel_with_jam_data(xlsx_file):
    """Импортирует данные о статитстике артикулов Джема из Excel файла"""
    excel_data_common = pd.read_excel(xlsx_file)
    column_list = excel_data_common.columns.tolist()
    sheet_names = pd.ExcelFile(xlsx_file).sheet_names
    if 'Инфо' in sheet_names and 'Детальная информация' in sheet_names:
        df_info = pd.read_excel(xlsx_file, sheet_name='Инфо', header=1)
        column_list = df_info.columns.tolist()
        selected_period_value = df_info.loc[df_info.iloc[:, 0]
                                            == 'Выбранный период', df_info.columns[1]].values[0]
        date_pattern = r'\d{4}-\d{2}-\d{2}'

        # Поиск всех совпадений
        dates = re.findall(date_pattern, selected_period_value)
        date_start = dates[0]
        date_finish = dates[1]

        df_statistic = pd.read_excel(
            xlsx_file, sheet_name='Детальная информация', header=1)
        excel_data = pd.DataFrame(df_statistic, columns=[
                                  'Артикул продавца',
                                  'Номенклатура',
                                  'Поисковый запрос',
                                  'Частота, шт',
                                  'Видимость, %',
                                  'Средняя позиция',
                                  'Медианная позиция',
                                  'Переходы в карточку',
                                  'Положили в корзину',
                                  'Конверсия в корзину, %',
                                  'Заказали, шт',
                                  'Конверсия в заказ, %'
                                  ])
        article_list = excel_data['Артикул продавца'].to_list()
        nom_list = excel_data['Номенклатура'].to_list()
        cluster_list = excel_data['Поисковый запрос'].to_list()
        frequency_list = excel_data['Частота, шт'].to_list()
        visibility_list = excel_data['Видимость, %'].to_list()
        average_position_list = excel_data['Средняя позиция'].to_list()
        median_position_list = excel_data['Медианная позиция'].to_list()
        go_to_card_list = excel_data['Переходы в карточку'].to_list()
        added_to_cart_list = excel_data['Положили в корзину'].to_list()
        conversion_to_cart_list = excel_data['Конверсия в корзину, %'].to_list(
        )
        ordered_list = excel_data['Заказали, шт'].to_list()
        conversion_to_order_list = excel_data['Конверсия в заказ, %'].to_list()

        for i in range(len(article_list)):
            article_obj = Articles.objects.filter(
                wb_seller_article=article_list[i])
            cluser_obj = add_keyphrase_to_db(cluster_list[i])
            # article_obj = Articles.objects.filter(
            #     wb_seller_article=article_list[i])
            # if len(article_obj) > 1:
            #     print(article_obj, len(article_obj))
            if len(article_obj) == 0:
                print(article_list[i])

            cluster = cluser_obj
            frequency = frequency_list[i]
            visibility = visibility_list[i]
            average_position = average_position_list[i]
            median_position = median_position_list[i]
            go_to_card = go_to_card_list[i]
            added_to_cart = added_to_cart_list[i]
            conversion_to_cart = conversion_to_cart_list[i]
            ordered = ordered_list[i]
            conversion_to_order = conversion_to_order_list[i]
            if article_obj.exists():
                views = int(frequency) * int(visibility) / 100
                if not JamMainArticleKeyWords.objects.filter(article=article_obj[0], cluster=cluster, date_start=date_start, date_finish=date_finish).exists():
                    JamMainArticleKeyWords(
                        article=article_obj[0],
                        cluster=cluster,
                        date_start=date_start,
                        date_finish=date_finish,
                        frequency=frequency,
                        visibility=visibility,
                        views=views,
                        average_position=average_position,
                        median_position=median_position,
                        go_to_card=go_to_card,
                        added_to_cart=added_to_cart,
                        conversion_to_cart=conversion_to_cart,
                        ordered=ordered,
                        conversion_to_order=conversion_to_order
                    ).save()
                else:
                    JamMainArticleKeyWords.objects.filter(
                        article=article_obj[0],
                        cluster=cluster,
                        date_start=date_start,
                        date_finish=date_finish).update(

                        frequency=frequency,
                        visibility=visibility,
                        views=views,
                        average_position=average_position,
                        median_position=median_position,
                        go_to_card=go_to_card,
                        added_to_cart=added_to_cart,
                        conversion_to_cart=conversion_to_cart,
                        ordered=ordered,
                        conversion_to_order=conversion_to_order
                    )

        # article_obj = Articles.objects.all().values('wb_nomenclature')
        # for nm in article_obj:
        #     if nm['wb_nomenclature'] != None:
        #         ls = Articles.objects.filter(
        #             wb_nomenclature=nm['wb_nomenclature'])
        #         if len(ls) > 1:
        #             print(ls, len(ls))

    else:
        return f'Вы пытались загрузить ошибочный файл {xlsx_file}.'
