from datetime import datetime, timedelta

from motivation.models import Selling
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg

from web_barcode.constants_file import CHAT_ID_ADMIN, bot

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


@sender_error_to_tg
def save_wildberries_sale_data_for_motivation(data, ur_lico, month, year):
    """Сохраняет данные по продажам Wildberries в базу продаж по подсчету мотивации"""
    now_date = datetime.now()
    wb_marketplace = CodingMarketplaces.objects.get(
        marketpalce='Wildberries')
    if Articles.objects.filter(wb_nomenclature=data['nmId']).exists():
        article_obj = Articles.objects.get(wb_nomenclature=data['nmId'])

        if Selling.objects.filter(lighter=article_obj,
                                  ur_lico=ur_lico,
                                  year=year,
                                  month=month,
                                  marketplace=wb_marketplace).exists():
            sell_obj = Selling.objects.get(lighter=article_obj,
                                           ur_lico=ur_lico,
                                           year=year,
                                           month=month,
                                           marketplace=wb_marketplace)
            sell_obj.summ += int(data['finishedPrice'])
            sell_obj.quantity += 1
            sell_obj.data = now_date
            sell_obj.save()

        else:
            Selling(
                lighter=article_obj,
                ur_lico=ur_lico,
                year=year,
                month=month,
                summ=data['finishedPrice'],
                quantity=1,
                data=now_date,
                marketplace=wb_marketplace).save()
    else:
        message = f'В базе данных нет артикула {data["nmId"]}. Не смог загрузить по нему продажи в базу данных для мотивации'
        bot.send_message(chat_id=CHAT_ID_ADMIN, text=message)
