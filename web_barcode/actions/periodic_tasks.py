from datetime import datetime

from api_request.wb_requests import (wb_action_details_info, wb_actions_first_list, wb_articles_in_action)
from celery_tasks.celery import app


from reklama.models import UrLico


from actions.models import Action, ArticleMayBeInAction
from actions.supplyment import add_article_may_be_in_action
from api_request.ozon_requests import ozon_actions_first_list, ozon_articles_in_action
from web_barcode.constants_file import (CHAT_ID_ADMIN, bot, header_ozon_dict,
                                        actions_info_users_list,
                                        header_wb_dict)
from database.models import CodingMarketplaces
from price_system.models import Articles


@app.task
def add_new_actions_wb_to_db():
    """Добавляет новую акцию ВБ в базу данных"""
    for ur_lico_obj in UrLico.objects.all():
        header  = header_wb_dict[ur_lico_obj.ur_lice_name]
        # Получаем информацию по новым акциям
        actions_data = wb_actions_first_list(header)
        actions_not_exist_str = ''
        if actions_data:
            actions_info = actions_data['data']['promotions']
            for action in actions_info:
                
                if not Action.objects.filter(ur_lico=ur_lico_obj, action_number=action['id']).exists():
                    message = (f"У Юр. лица {ur_lico_obj.ur_lice_name} появилась новая акция ВБ: "
                                f"{action['id']}: {action['name']}.\n"
                                f"Дата начала: {datetime.strptime(action['startDateTime'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')}.\n"
                                f"Дата завершения {datetime.strptime(action['endDateTime'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')}.")
                    for chat_id in actions_info_users_list:
                        bot.send_message(chat_id=chat_id,
                             text=message)
                    actions_not_exist_str += f"promotionIDs={action['id']}&"
        if actions_not_exist_str:
            # Получаем детальную информацию по новым акциям
            actions_details = wb_action_details_info(header, actions_not_exist_str)
            if actions_details and 'data' in actions_details:
                for detail in actions_details['data']['promotions']:
                    # Получаем инормацию по артикулам, которые могут участвовать в акции
                    article_action_data = wb_articles_in_action(header, action['id'])
                    articles_amount = 0
                    if article_action_data:
                        # Смотрим кол-во артикулов, которые могут участвовать в акции
                        articles_amount = len(article_action_data['data']['nomenclatures'])
                    # Сохраняем новую акцию в базу
                    action_obj = Action(
                        ur_lico=ur_lico_obj,
                        marketplace=CodingMarketplaces.objects.get(marketpalce='Wildberries'),
                        action_number = detail['id'],
                        name = detail['name'],
                        description = detail['description'],
                        date_start = detail['startDateTime'],
                        date_finish = detail['endDateTime'],
                        action_type = detail['type'],
                        articles_amount = articles_amount
                    ).save()
                    # Сохраняем артикулы, которые могут участвовать в акции
                    add_article_may_be_in_action(ur_lico_obj, article_action_data, action_obj)
                   

@app.task
def add_new_actions_ozon_to_db():
    """Добавляет новую акцию ОЗОН в базу данных"""
    for ur_lico_obj in UrLico.objects.all():
        header  = header_ozon_dict[ur_lico_obj.ur_lice_name]
        # Получаем информацию по новым акциям
        actions_data = ozon_actions_first_list(header)
        new_action_list = []
        if actions_data:
            actions_info = actions_data['result']
            for action in actions_info:
                # if not Action.objects.filter(ur_lico=ur_lico_obj, action_number=action['id']).exists():
                    # message = (f"У Юр. лица {ur_lico_obj.ur_lice_name} появилась новая акция: "
                    #             f"{action['id']}: {action['name']}.\n"
                    #             f"Дата начала: {datetime.strptime(action['startDateTime'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')}.\n"
                    #             f"Дата завершения {datetime.strptime(action['endDateTime'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')}.")
                    # for chat_id in actions_info_users_list:
                    #     bot.send_message(chat_id=chat_id,
                    #          text=message)
                    new_action_list.append(action['id'])

                    search_params = {'ur_lico': ur_lico_obj, 'marketplace': CodingMarketplaces.objects.get(marketpalce='Ozon'), 'action_number': action['id']}
                    values_for_update = {
                        'description': action['description'],
                        'date_start': action['date_start'],
                        'date_finish': action['date_end'],
                        'articles_amount': action['potential_products_count']
                    }
                    print(action['id'], ur_lico_obj)
                    Action.objects.update_or_create(
                                defaults=values_for_update, **search_params
                            )
        
        if new_action_list:
            for action_number in new_action_list:
                action_obj = Action.objects.get(
                    ur_lico=ur_lico_obj, 
                    marketplace=CodingMarketplaces.objects.get(marketpalce='Ozon'), 
                    action_number=action_number)
                articles_info = ozon_articles_in_action(header, action_number)
                if articles_info:
                    print('len(articles_info)', len(articles_info))
                    for article in articles_info:
                        if Articles.objects.filter(company=ur_lico_obj.ur_lice_name, ozon_product_id=article['id']).exists():
                            articles_obj = Articles.objects.filter(company=ur_lico_obj.ur_lice_name, ozon_product_id=article['id'])
                            if len(articles_obj) > 1:
                                message = f"У артикулов {articles_obj}, совпдают product_id от Озона: {article['id']}"  
                                bot.send_message(chat_id=CHAT_ID_ADMIN,
                                 text=message[:4000])
                            article_obj = Articles.objects.filter(company=ur_lico_obj.ur_lice_name, ozon_product_id=article['id'])[0]
                            action_discount = (article['price'] - article['max_action_price']) / article['price'] * 100
                            search_params = {'action': action_obj, 'article': article_obj}
                            values_for_update = {
                                'action_price': article['max_action_price'],
                                'action_discount': round(action_discount, 2)
                            }
                            ArticleMayBeInAction.objects.update_or_create(
                                defaults=values_for_update, **search_params
                            )
