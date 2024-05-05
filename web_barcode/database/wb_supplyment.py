from datetime import datetime, timedelta

from motivation.models import Selling
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg

from .models import CodingMarketplaces, WildberriesSales


@sender_error_to_tg
def wb_save_sales_data_to_database(data, ur_lico, month, year):
    """Записывает данные по продажам с Wildberries в базу данных"""
    WildberriesSales(
        date=data['date'],
        last_change_date=data['lastChangeDate'],
        warehouse_name=data['warehouseName'],
        country_name=data['countryName'],
        oblast_okrug_name=data['oblastOkrugName'],
        region_name=data['regionName'],
        supplier_article=data['supplierArticle'],
        nm_id=data['nmId'],
        barcode=data['barcode'],
        category=data['category'],
        subject=data['subject'],
        brand=data['brand'],
        tech_size=data['techSize'],
        income_id=data['incomeID'],
        is_supply=data['isSupply'],
        is_realization=data['isRealization'],
        total_price=data['totalPrice'],
        discount_percent=data['discountPercent'],
        spp=data['spp'],
        payment_sale_amount=data['paymentSaleAmount'],
        for_pay=data['forPay'],
        finished_price=data['finishedPrice'],
        price_with_disc=data['priceWithDisc'],
        sale_id=data['saleID'],
        order_type=data['orderType'],
        sticker=data['sticker'],
        g_number=data['gNumber'],
        srid=data['srid'],
        ur_lico=ur_lico,
        month=month,
        year=year
    ).save()


# @sender_error_to_tg
def save_wildberries_sale_data_for_motivation():
    """Сохраняет данные по продажам Wildberries в базу продаж по подсчету мотивации"""
    now_date = datetime.now() - timedelta(days=20)
    filter_month = now_date.strftime('%m')
    current_year = now_date.strftime('%Y')

    wb_marketplace = CodingMarketplaces.objects.get(
        marketpalce='Wildberries')
    article_data = Articles.objects.all()
    for article in article_data:
        article_data = WildberriesSales.objects.filter(
            nm_id=article.wb_nomenclature, month=filter_month, year=current_year).values('finished_price')
        summ_money = 0
        quantity = len(article_data)
        for i in article_data:
            summ_money += i['finished_price']
        if Selling.objects.filter(lighter=article,
                                  ur_lico=article.company,
                                  year=current_year,
                                  month=filter_month,
                                  marketplace=wb_marketplace).exists():
            Selling.objects.filter(lighter=article,
                                   ur_lico=article.company,
                                   year=current_year,
                                   month=filter_month,
                                   marketplace=wb_marketplace).update(summ=summ_money,
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
                marketplace=wb_marketplace).save()
