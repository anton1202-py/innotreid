from price_system.supplyment import sender_error_to_tg

from .models import WildberriesSales


# @sender_error_to_tg
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
