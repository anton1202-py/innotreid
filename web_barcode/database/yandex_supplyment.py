import time
from datetime import datetime, timedelta

from motivation.models import Selling
from price_system.models import Articles
from price_system.supplyment import sender_error_to_tg

from web_barcode.constants_file import CHAT_ID_ADMIN, bot

from .models import (CodingMarketplaces, OzonDailyOrders, OzonMonthlySalesData,
                     OzonSales, YandexDailyOrders)


@sender_error_to_tg
def save_yandex_daily_orders(data, order_date, month, year, ur_lico):
    """Сохраняет данные по заказам Yandex в базу данных"""
    for order_article in data['items']:
        yandex_sku = order_article['marketSku']
        amount = order_article['count']
        seller_article = order_article['shopSku']
        price_list = order_article['prices']
        order_summ = 0
        if order_article['prices']:
            for price in price_list:
                order_summ += price['total']

        YandexDailyOrders(
            order_date_period=order_date,
            month=month,
            year=year,
            yandex_sku=yandex_sku,
            seller_article=seller_article,
            amount=amount,
            order_summ=round(order_summ),
            ur_lico=ur_lico
        ).save()


@sender_error_to_tg
def save_yandex_daily_orders_data_for_motivation(data, order_date, month, year, ur_lico):
    """Сохраняет данные по заказам Озон в базу по подсчету мотивации"""
    for order_article in data['items']:
        yandex_marketplace = CodingMarketplaces.objects.get(
            marketpalce='Yandex Market')
        article_obj = ''
        yandex_sku = order_article['marketSku']
        amount = order_article['count']
        seller_article = order_article['shopSku']
        price_list = order_article['prices']
        order_summ = 0
        if order_article['prices']:
            for price in price_list:
                order_summ += price['total']
        if Articles.objects.filter(yandex_sku=yandex_sku).exists():
            article_obj = Articles.objects.get(
                yandex_sku=yandex_sku)

        if article_obj:
            if Selling.objects.filter(lighter=article_obj,
                                      ur_lico=ur_lico,
                                      year=year,
                                      month=month,
                                      marketplace=yandex_marketplace).exists():
                sell_obj = Selling.objects.get(lighter=article_obj,
                                               ur_lico=ur_lico,
                                               year=year,
                                               month=month,
                                               marketplace=yandex_marketplace)
                sell_obj.summ += round(order_summ)
                sell_obj.quantity += amount
                sell_obj.data = order_date
                sell_obj.save()

            else:
                Selling(
                    lighter=article_obj,
                    ur_lico=ur_lico,
                    year=year,
                    month=month,
                    summ=order_summ,
                    quantity=amount,
                    data=order_date,
                    marketplace=yandex_marketplace).save()
        else:
            message = f"В базе данных Yandex нет артикула {seller_article} {yandex_sku} {ur_lico}. Не смог загрузить по нему продажи в базу данных для мотивации"
            print(message)
            time.sleep(1)
            bot.send_message(chat_id=CHAT_ID_ADMIN, text=message)
