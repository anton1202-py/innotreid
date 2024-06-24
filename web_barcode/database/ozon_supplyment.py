import time
from datetime import datetime, timedelta

from motivation.models import Selling
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg

from web_barcode.constants_file import CHAT_ID_ADMIN, bot

from .models import (CodingMarketplaces, OzonDailyOrders, OzonMonthlySalesData,
                     OzonSales)


@sender_error_to_tg
def ozon_main_process_sale_data(main_data, ur_lico, month_report, year_report):
    """Обрабатывает главные данные отчета по продажам с Ozon"""
    main_date_info = main_data['result']['header']

    start_date_period = main_date_info['start_date']
    finish_date_period = main_date_info['stop_date']
    number_report = main_date_info['number']
    doc_date = main_date_info['doc_date']
    doc_amount = main_date_info['doc_amount']
    vat_amount = main_date_info['vat_amount']
    sale_article_info = main_data['result']['rows']

    main_sale_data_dict = {}
    main_sale_data_dict['start_date_period'] = start_date_period
    main_sale_data_dict['finish_date_period'] = finish_date_period
    main_sale_data_dict['number_report'] = number_report
    main_sale_data_dict['doc_date'] = doc_date
    main_sale_data_dict['doc_amount'] = doc_amount
    main_sale_data_dict['vat_amount'] = vat_amount
    main_sale_data_dict['ur_lico'] = ur_lico
    main_sale_data_dict['month'] = month_report
    main_sale_data_dict['year'] = year_report

    ozon_save_main_sale_data_in_database(main_sale_data_dict)
    ozon_article_sale_data(sale_article_info, ur_lico, start_date_period, finish_date_period,
                           number_report, month_report, year_report)


@sender_error_to_tg
def ozon_article_sale_data(sale_article_info, ur_lico, start_date_period, finish_date_period,
                           number_report, month_report, year_report):
    """Обрабатывает данные артикулов отчета по продажам с Ozon"""
    for data in sale_article_info:
        func_data_dict = {}
        row_number = data['rowNumber']
        if row_number != 0:

            offer_id = data['item']['offer_id']
            sku = data['item']['sku']
            barcode = data['item']['barcode']
            name = data['item']['name']

            seller_price_per_instance = data['seller_price_per_instance']

            amount = data['delivery_commission']['amount']
            bonus = data['delivery_commission']['bonus']
            commission = data['delivery_commission']['commission']
            compensation = data['delivery_commission']['compensation']
            price_per_instance = data['delivery_commission']['price_per_instance']
            quantity = data['delivery_commission']['quantity']
            standard_fee = data['delivery_commission']['standard_fee']
            stars = data['delivery_commission']['stars']
            total = data['delivery_commission']['total']

            commission_ratio = data['commission_ratio']

            if data['return_commission']:
                return_amount = data['return_commission']['amount']
                return_bonus = data['return_commission']['bonus']
                return_commission = data['return_commission']['commission']
                return_compensation = data['return_commission']['compensation']
                return_price_per_instance = data['return_commission']['price_per_instance']
                return_quantity = data['return_commission']['quantity']
                return_standard_fee = data['return_commission']['standard_fee']
                return_stars = data['return_commission']['stars']
                return_total = data['return_commission']['total']
            else:
                return_amount = None
                return_bonus = None
                return_commission = None
                return_compensation = None
                return_price_per_instance = None
                return_quantity = None
                return_standard_fee = None
                return_stars = None
                return_total = None

        func_data_dict['start_date_period'] = start_date_period
        func_data_dict['finish_date_period'] = finish_date_period
        func_data_dict['number_report'] = number_report
        func_data_dict['row_number'] = row_number
        func_data_dict['offer_id'] = offer_id
        func_data_dict['sku'] = sku
        func_data_dict['barcode'] = barcode
        func_data_dict['name'] = name
        func_data_dict['seller_price_per_instance'] = seller_price_per_instance
        func_data_dict['amount'] = amount
        func_data_dict['bonus'] = bonus
        func_data_dict['commission'] = commission
        func_data_dict['compensation'] = compensation
        func_data_dict['price_per_instance'] = price_per_instance
        func_data_dict['quantity'] = quantity
        func_data_dict['standard_fee'] = standard_fee
        func_data_dict['stars'] = stars
        func_data_dict['total'] = total
        func_data_dict['commission_ratio'] = commission_ratio
        func_data_dict['return_amount'] = return_amount
        func_data_dict['return_bonus'] = return_bonus
        func_data_dict['return_commission'] = return_commission
        func_data_dict['return_compensation'] = return_compensation
        func_data_dict['return_price_per_instance'] = return_price_per_instance
        func_data_dict['return_quantity'] = return_quantity
        func_data_dict['return_standard_fee'] = return_standard_fee
        func_data_dict['return_stars'] = return_stars
        func_data_dict['return_total'] = return_total
        func_data_dict['ur_lico'] = ur_lico,
        func_data_dict['month'] = month_report
        func_data_dict['year'] = year_report
        ozon_save_article_sale_in_database(func_data_dict)


@sender_error_to_tg
def ozon_save_article_sale_in_database(func_data_dict):
    """Сохранет информацию о продажах артикула"""
    OzonSales(
        start_date_period=func_data_dict['start_date_period'],
        finish_date_period=func_data_dict['finish_date_period'],
        number_report=func_data_dict['number_report'],
        row_number=func_data_dict['row_number'],
        offer_id=func_data_dict['offer_id'],
        sku=func_data_dict['sku'],
        barcode=func_data_dict['barcode'],
        name=func_data_dict['name'],
        seller_price_per_instance=func_data_dict['seller_price_per_instance'],
        amount=func_data_dict['amount'],
        bonus=func_data_dict['bonus'],
        commission=func_data_dict['commission'],
        compensation=func_data_dict['compensation'],
        price_per_instance=func_data_dict['price_per_instance'],
        quantity=func_data_dict['quantity'],
        standard_fee=func_data_dict['standard_fee'],
        stars=func_data_dict['stars'],
        total=func_data_dict['total'],
        commission_ratio=func_data_dict['commission_ratio'],
        return_amount=func_data_dict['return_amount'],
        return_bonus=func_data_dict['return_bonus'],
        return_commission=func_data_dict['return_commission'],
        return_compensation=func_data_dict['return_compensation'],
        return_price_per_instance=func_data_dict['return_price_per_instance'],
        return_quantity=func_data_dict['return_quantity'],
        return_standard_fee=func_data_dict['return_standard_fee'],
        return_stars=func_data_dict['return_stars'],
        return_total=func_data_dict['return_total'],
        ur_lico=func_data_dict['ur_lico'],
        month=func_data_dict['month'],
        year=func_data_dict['year']
    ).save()


@sender_error_to_tg
def ozon_save_main_sale_data_in_database(main_sale_data_dict):
    """Сохранет общую информацию о продажах за месяц"""
    OzonMonthlySalesData(
        start_date_period=main_sale_data_dict['start_date_period'],
        finish_date_period=main_sale_data_dict['finish_date_period'],
        number_report=main_sale_data_dict['number_report'],
        doc_date=main_sale_data_dict['doc_date'],
        doc_amount=main_sale_data_dict['doc_amount'],
        vat_amount=main_sale_data_dict['vat_amount'],
        month=main_sale_data_dict['month'],
        year=main_sale_data_dict['year'],
        ur_lico=main_sale_data_dict['ur_lico'],
    ).save()


@sender_error_to_tg
def save_ozon_sale_data_for_motivation():
    """Сохраняет данные по продажам Озон в базу продаж по подсчету мотивации"""
    now_date = datetime.now() - timedelta(days=20)
    filter_month = now_date.strftime('%m')
    current_year = now_date.strftime('%Y')

    ozon_marketplace = CodingMarketplaces.objects.get(marketpalce='Ozon')
    article_data = Articles.objects.all()
    for article in article_data:

        article_data = OzonSales.objects.filter(
            offer_id=article.ozon_seller_article, month=filter_month, year=current_year).values('total', 'quantity')

        summ_money = 0
        quantity = 0
        for i in article_data:
            quantity += i['quantity']
            summ_money += i['total']
        if Selling.objects.filter(lighter=article,
                                  ur_lico=article.company,
                                  year=current_year,
                                  month=filter_month,
                                  marketplace=ozon_marketplace).exists():
            Selling.objects.filter(lighter=article,
                                   ur_lico=article.company,
                                   year=current_year,
                                   month=filter_month,
                                   marketplace=ozon_marketplace).update(summ=summ_money,
                                                                        quantity=quantity,
                                                                        data=now_date,)
        else:
            Selling(
                lighter=article,
                ur_lico=article.company,
                year=current_year,
                month=filter_month,
                summ=summ_money,
                quantity=quantity,
                data=now_date,
                marketplace=ozon_marketplace).save()


@sender_error_to_tg
def save_ozon_daily_orders(data, order_date, month, year, ur_lico):
    """Сохраняет данные по заказам Озон в базу данных"""
    if data['metrics'][0] != 0:
        ozon_sku = data['dimensions'][0]['id']
        amount = data['metrics'][1]
        order_summ = data['metrics'][0]
        OzonDailyOrders(
            order_date_period=order_date,
            month=month,
            year=year,
            ozon_sku=ozon_sku,
            amount=amount,
            order_summ=order_summ,
            ur_lico=ur_lico
        ).save()


@sender_error_to_tg
def save_ozon_daily_orders_data_for_motivation(data, order_date, month, year, ur_lico):
    """Сохраняет данные по заказам Озон в базу по подсчету мотивации"""
    if data['metrics'][0] > 0:
        ozon_marketplace = CodingMarketplaces.objects.get(marketpalce='Ozon')
        article_obj = ''
        if Articles.objects.filter(ozon_sku=data['dimensions'][0]['id']).exists():
            article_obj = Articles.objects.get(
                ozon_sku=data['dimensions'][0]['id'])
        elif Articles.objects.filter(ozon_fbo_sku_id=data['dimensions'][0]['id']).exists():
            article_obj = Articles.objects.get(
                ozon_fbo_sku_id=data['dimensions'][0]['id'])
        elif Articles.objects.filter(ozon_fbs_sku_id=data['dimensions'][0]['id']).exists():
            article_obj = Articles.objects.get(
                ozon_fbs_sku_id=data['dimensions'][0]['id'])
        if article_obj:
            if Selling.objects.filter(lighter=article_obj,
                                      ur_lico=ur_lico,
                                      year=year,
                                      month=month,
                                      marketplace=ozon_marketplace).exists():
                sell_obj = Selling.objects.get(lighter=article_obj,
                                               ur_lico=ur_lico,
                                               year=year,
                                               month=month,
                                               marketplace=ozon_marketplace)
                sell_obj.summ += int(data['metrics'][0])
                sell_obj.quantity += data['metrics'][1]
                sell_obj.data = order_date
                sell_obj.save()

            else:
                Selling(
                    lighter=article_obj,
                    ur_lico=ur_lico,
                    year=year,
                    month=month,
                    summ=int(data['metrics'][0]),
                    quantity=int(data['metrics'][1]),
                    data=order_date,
                    marketplace=ozon_marketplace).save()
        else:
            message = f"В базе данных ОЗОН нет артикула {data['dimensions'][0]['name']} {data['metrics'][0]} {data['metrics'][1]} {ur_lico} {data['dimensions'][0]['id']}. Не смог загрузить по нему продажи в базу данных для мотивации"
            time.sleep(1)
            bot.send_message(chat_id=CHAT_ID_ADMIN, text=message)
