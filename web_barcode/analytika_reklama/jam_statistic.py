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
        settings_indicator = df_info.loc[df_info.iloc[:, 0]
                                            == 'Показывать запросы, по которым больше всего', df_info.columns[1]].values[0]
        date_object = datetime.strptime(date_start, "%Y-%m-%d")
                #     # Получение номера недели
        week_number = date_object.isocalendar()[1]
        year = date_object.year
        df_statistic = pd.read_excel(
            xlsx_file, sheet_name='Детальная информация', header=1)
        excel_data = pd.DataFrame(df_statistic, columns=[
                                  'Артикул продавца',
                                  'Номенклатура',
                                  'Поисковый запрос',

                                  'Частота, шт',
                                  'Частота, шт (предыдущий период)',

                                  'Видимость, %',
                                  'Видимость, % (предыдущий период)',

                                  'Средняя позиция',
                                  'Средняя позиция (предыдущий период)',

                                  'Медианная позиция',
                                  'Медианная позиция (предыдущий период)',

                                  'Переходы в карточку',
                                  'Переходы в карточку (предыдущий период)',
                                  'Переходы в карточку больше, чем у n% карточек конкурентов, %',
                                  
                                  'Положили в корзину',
                                  'Положили в корзину (предыдущий период)',
                                  'Положили в корзину больше, чем n% карточек конкурентов, %',

                                  'Конверсия в корзину, %',
                                  'Конверсия в корзину, % (предыдущий период)',
                                  'Конверсия в корзину больше, чем у n% карточек конкурентов, %',

                                  'Заказали, шт',
                                  'Заказали, шт (предыдущий период)',
                                  'Заказали больше, чем n% карточек конкурентов, %',

                                  'Конверсия в заказ, %',
                                  'Конверсия в заказ, % (предыдущий период)',
                                  'Конверсия в заказ больше, чем у n% карточек конкурентов, %',
                                  ])
        article_list = excel_data['Артикул продавца'].to_list()
        nom_list = excel_data['Номенклатура'].to_list()
        cluster_list = excel_data['Поисковый запрос'].to_list()

        frequency_list = excel_data['Частота, шт'].to_list()
        frequency_before_list = excel_data['Частота, шт (предыдущий период)'].to_list()

        visibility_list = excel_data['Видимость, %'].to_list()
        visibility_before_list = excel_data['Видимость, % (предыдущий период)'].to_list()

        average_position_list = excel_data['Средняя позиция'].to_list()
        average_position_before_list = excel_data['Средняя позиция (предыдущий период)'].to_list()

        median_position_list = excel_data['Медианная позиция'].to_list()
        median_position_before_list = excel_data['Медианная позиция (предыдущий период)'].to_list()

        go_to_card_list = excel_data['Переходы в карточку'].to_list()
        go_to_card_before_list = excel_data['Переходы в карточку (предыдущий период)'].to_list()
        go_to_card_more_than_list = excel_data['Переходы в карточку больше, чем у n% карточек конкурентов, %'].to_list()


        added_to_cart_list = excel_data['Положили в корзину'].to_list()
        added_to_cart_before_list = excel_data['Положили в корзину (предыдущий период)'].to_list()
        added_to_cart_more_than_list = excel_data['Положили в корзину больше, чем n% карточек конкурентов, %'].to_list()
        
        conversion_to_cart_list = excel_data['Конверсия в корзину, %'].to_list()
        conversion_to_cart_before_list = excel_data['Конверсия в корзину, % (предыдущий период)'].to_list()
        conversion_to_cart_before_than_list = excel_data['Конверсия в корзину больше, чем у n% карточек конкурентов, %'].to_list()

        ordered_list = excel_data['Заказали, шт'].to_list()
        ordered_before_list = excel_data['Заказали, шт (предыдущий период)'].to_list()
        ordered_more_than_list = excel_data['Заказали больше, чем n% карточек конкурентов, %'].to_list()

        conversion_to_order_list = excel_data['Конверсия в заказ, %'].to_list()
        conversion_to_order_before_list = excel_data['Конверсия в заказ, % (предыдущий период)'].to_list()
        conversion_to_order_more_than_list = excel_data['Конверсия в заказ больше, чем у n% карточек конкурентов, %'].to_list()
        update_list = []
        create_list = []
        x = len(nom_list)
        print(len(nom_list))
        for i in range(len(nom_list)):
            article_obj = Articles.objects.filter(
                wb_nomenclature=nom_list[i])
            cluser_obj = add_keyphrase_to_db(cluster_list[i])
            # article_obj = Articles.objects.filter(
            #     wb_seller_article=article_list[i])
            # if len(article_obj) > 1:
            #     print(article_obj, len(article_obj))
            if len(article_obj) == 0:
                print(article_list[i])
            if article_obj.exists():
                cluster = cluser_obj

                frequency = frequency_list[i]
                frequency_before = frequency_before_list[i]

                visibility = visibility_list[i]
                visibility_before = visibility_before_list[i]

                average_position = average_position_list[i]
                average_position_before = average_position_before_list[i]

                median_position = median_position_list[i]
                median_position_before = median_position_before_list[i]

                go_to_card = go_to_card_list[i]
                go_to_card_before = go_to_card_before_list[i]
                go_to_card_more_than = go_to_card_more_than_list[i]

                added_to_cart = added_to_cart_list[i]
                added_to_cart_before = added_to_cart_before_list[i]
                added_to_cart_more_than = added_to_cart_more_than_list[i]

                conversion_to_cart = conversion_to_cart_list[i]
                conversion_to_cart_before = conversion_to_cart_before_list[i]
                conversion_to_cart_more_than = conversion_to_cart_before_than_list[i]

                ordered = ordered_list[i]
                ordered_before = ordered_before_list[i]
                ordered_more_than = ordered_more_than_list[i]

                conversion_to_order = conversion_to_order_list[i]
                conversion_to_order_before = conversion_to_order_before_list[i]
                conversion_to_order_more_than = conversion_to_order_more_than_list[i]

                if article_obj.exists():
                    views = int(frequency) * int(visibility) / 100
                    views_before = int(frequency_before) * int(visibility_before) / 100
                    
                    if not JamMainArticleKeyWords.objects.filter(article=article_obj[0],
                            cluster=cluster,
                            date_start=date_start,
                            date_finish=date_finish,
                            week_number=week_number,
                            settings_indicator=settings_indicator).exists():
                        JamMainArticleKeyWords(
                            article=article_obj[0],
                            cluster=cluster,
                            date_start=date_start,
                            date_finish=date_finish,
                            week_number=week_number,
                            year=year,

                            settings_indicator=settings_indicator,

                            frequency=frequency,
                            frequency_before=frequency_before,

                            visibility=visibility,
                            visibility_before=visibility_before,

                            views=views,
                            views_before=views_before,

                            average_position=average_position,
                            average_position_before=average_position_before,

                            median_position=median_position,
                            median_position_before=median_position_before,

                            go_to_card=go_to_card,
                            go_to_card_before=go_to_card_before,
                            go_to_card_more_than=go_to_card_more_than,

                            added_to_cart=added_to_cart,
                            added_to_cart_before=added_to_cart_before,
                            added_to_cart_more_than=added_to_cart_more_than,

                            conversion_to_cart=conversion_to_cart,
                            conversion_to_cart_before=conversion_to_cart_before,
                            conversion_to_cart_more_than=conversion_to_cart_more_than,

                            ordered=ordered,
                            ordered_before=ordered_before,
                            ordered_more_than=ordered_more_than,

                            conversion_to_order=conversion_to_order,
                            conversion_to_order_before=conversion_to_order_before,
                            conversion_to_order_more_than=conversion_to_order_more_than
                        ).save()
                        # create_list.append(jam_obj)
                    # else:
                    #     jam_update_obj = JamMainArticleKeyWords.objects.get(
                    #         article=article_obj[0],
                    #         cluster=cluster,
                    #         date_start=date_start,
                    #         date_finish=date_finish,
                    #         week_number=week_number,
                    #         settings_indicator=settings_indicator)
                    #     jam_update_obj.visibility=visibility
                    #     jam_update_obj.visibility_before=visibility_before
                    #     jam_update_obj.views=views
                    #     jam_update_obj.views_before=views_before
                    #     jam_update_obj.average_position=average_position
                    #     jam_update_obj.average_position_before=average_position_before
                    #     jam_update_obj.median_position=median_position
                    #     jam_update_obj.median_position_before=median_position_before
                    #     jam_update_obj.go_to_card=go_to_card
                    #     jam_update_obj.go_to_card_before=go_to_card_before
                    #     jam_update_obj.go_to_card_more_than=go_to_card_more_than
                    #     jam_update_obj.added_to_cart=added_to_cart
                    #     jam_update_obj.added_to_cart_before=added_to_cart_before
                    #     jam_update_obj.added_to_cart_more_than=added_to_cart_more_than
                    #     jam_update_obj.conversion_to_cart=conversion_to_cart
                    #     jam_update_obj.conversion_to_cart_before=conversion_to_cart_before
                    #     jam_update_obj.conversion_to_cart_more_than=conversion_to_cart_more_than
                    #     jam_update_obj.ordered=ordered
                    #     jam_update_obj.ordered_before=ordered_before
                    #     jam_update_obj.ordered_more_than=ordered_more_than
                    #     jam_update_obj.conversion_to_order=conversion_to_order
                    #     jam_update_obj.conversion_to_order_before=conversion_to_order_before
                    #     jam_update_obj.conversion_to_order_more_than=conversion_to_order_more_than
                    #     jam_update_obj.save()
                        # update_list.append(jam_update_obj)
            
        print(xlsx_file)
        if update_list:
            JamMainArticleKeyWords.objects.bulk_update(
                update_list, ['visibility', 
                              'visibility_before',
                              'views',
                              'views_before',
                              'average_position',
                              'average_position_before',
                              'median_position',
                              'median_position_before',
                              'go_to_card',
                              'go_to_card_before',
                              'go_to_card_more_than',
                              'added_to_cart',
                              'added_to_cart_before',
                              'added_to_cart_more_than',
                              'conversion_to_cart',
                              'conversion_to_cart_before',
                              'conversion_to_cart_more_than',
                              'ordered',
                              'ordered_before',
                              'ordered_more_than',
                              'conversion_to_order',
                              'conversion_to_order_before',
                              'conversion_to_order_more_than'])
        if create_list:
            JamMainArticleKeyWords.objects.bulk_create(create_list)
        print('Сохранил', xlsx_file)
        

    else:
        return f'Вы пытались загрузить ошибочный файл {xlsx_file}.'
