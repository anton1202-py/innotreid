from datetime import datetime

from django.db import models
from django.urls import reverse


class Articles(models.Model):
    common_article = models.CharField(
        verbose_name='Общий артикул',
        max_length=50,
        unique=True,
        null=True
    )
    title = models.CharField(
        verbose_name='Название',
        max_length=100,
        null=True,
    )
    article_seller_wb = models.CharField(
        verbose_name='Артикул постащика на WB',
        max_length=100,
        null=True,
    )
    article_wb_nomenclature = models.PositiveBigIntegerField(
        verbose_name='Номенклатура WB',
        null=True,
    )
    barcode_wb = models.PositiveBigIntegerField(
        verbose_name='Баркод WB',
        null=True,
    )
    article_seller_ozon = models.CharField(
        verbose_name='Артикул поставщика на OZON',
        max_length=100,
        null=True,
    )
    ozon_product_id = models.PositiveBigIntegerField(
        verbose_name='OZON Product ID',
        null=True,
    )
    fbo_ozon_sku_id = models.PositiveBigIntegerField(
        verbose_name='FBO OZON SKU ID',
        null=True,
    )
    fbs_ozon_sku_id = models.PositiveBigIntegerField(
        verbose_name='FBS OZON SKU ID',
        null=True,
    )
    barcode_ozon = models.PositiveBigIntegerField(
        verbose_name='Баркод OZON',
        null=True,
    )
    article_seller_yandex = models.CharField(
        verbose_name='Артикул поставщика на YANDEX',
        max_length=100,
        null=True,
    )
    barcode_yandex = models.PositiveBigIntegerField(
        verbose_name='Баркод YANDEX',
        null=True,
    )
    sku_yandex = models.PositiveBigIntegerField(
        verbose_name='SKU YANDEX',
        null=True,
    )
    multiplicity = models.PositiveSmallIntegerField(
        verbose_name='Кратность',
        null=True,
    )

    def __str__(self):
        return self.common_article

    def get_absolute_url(self):
        return f'/database/{self.id}'

    class Meta:
        verbose_name = 'Артикул'
        verbose_name_plural = 'Артикулы'


class CodingMarketplaces(models.Model):
    marketpalce = models.CharField(
        verbose_name='Название маркетплейса',
        max_length=15,
    )

    def __str__(self):
        return self.marketpalce

    class Meta:
        verbose_name = 'Код маркетплейса'
        verbose_name_plural = 'Коды маркетплейсов'


class CodingWbStock(models.Model):
    wb_stock = models.CharField(
        verbose_name='Название склада WB',
        max_length=40,
    )

    def __str__(self):
        return self.wb_stock

    class Meta:
        verbose_name = 'Название склада WB'
        verbose_name_plural = 'Название склада WB'


class WildberriesStocks(models.Model):
    pub_date = models.DateField(
        verbose_name='Дата',
        auto_now_add=True
    )
    seller_article_wb = models.CharField(
        verbose_name='Артикул продавца на WB',
        max_length=50,
        null=True
    )
    article_wb = models.CharField(
        verbose_name='Артикул маркетплейса',
        max_length=50,
    )
    code_stock = models.ForeignKey(
        CodingWbStock,
        verbose_name='Код склада WB',
        on_delete=models.PROTECT,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Склады Wildberries'
        verbose_name_plural = 'Склады Wildberries'


class ShelvingStocks(models.Model):
    task_start_date = models.DateTimeField(
        verbose_name='Дата постановки задания',
        null=True
    )
    task_finish_date = models.DateTimeField(
        verbose_name='Дата выполнения задания',
        null=True
    )
    seller_article_wb = models.CharField(
        verbose_name='Артикул продавца на WB',
        max_length=50,
        null=True
    )
    seller_article = models.CharField(
        verbose_name='Артикул продавца',
        max_length=50,
    )
    shelf_number = models.CharField(
        verbose_name='Номер полки',
        max_length=50,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Остаток на полке',
    )

    def save(self, *args, **kwargs):
        if self.amount <= 3:
            now = datetime.now()
            time_now = now.strftime("%Y-%m-%d %H:%M:%S")
            self.task_start_date = time_now
            self.task_finish_date = None
        super(ShelvingStocks, self).save(*args, **kwargs)

    def get_absolute_url(self):  # new
        return reverse('stock-shelving')

    def __str__(self):
        return (f'{self.task_start_date} - {self.seller_article}'
                f' - {self.shelf_number} - {self.amount}')

    class Meta:
        verbose_name = 'Склад на стеллажах'
        verbose_name_plural = 'Склад на стеллажах'


class Reviews(models.Model):
    pub_date = models.DateField(
        verbose_name='Дата отзыва'
    )
    article_marketplace = models.CharField(
        verbose_name='Артикул маркетплейса',
        max_length=50,
    )
    code_marketplace = models.ForeignKey(
        CodingMarketplaces,
        verbose_name='Код маркетплейса',
        on_delete=models.PROTECT,
    )
    text = models.TextField(
        verbose_name='Отзыв на товар',
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'


class Stocks(models.Model):
    pub_date = models.DateField(
        verbose_name='Дата',
        auto_now_add=True
    )
    seller_article = models.CharField(
        verbose_name='Артикул продавца',
        max_length=50,
        null=True
    )
    article_marketplace = models.CharField(
        verbose_name='Артикул маркетплейса',
        max_length=50,
    )
    code_marketplace = models.ForeignKey(
        CodingMarketplaces,
        verbose_name='Код маркетплейса',
        on_delete=models.PROTECT,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
    )

    def __str__(self):
        return self.article_marketplace, self.amount

    class Meta:
        verbose_name = 'Склад'
        verbose_name_plural = 'Склад'


class Sales(models.Model):
    pub_date = models.DateField(
        verbose_name='Дата',
    )
    article_marketplace = models.CharField(
        verbose_name='Артикул маркетплейса',
        max_length=50,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
    )
    avg_price_sale = models.FloatField(
        verbose_name='Средняя цена',
    )
    sum_sale = models.IntegerField(
        verbose_name='Сумма продажи',
    )
    sum_pay = models.IntegerField(
        verbose_name='Сумма выплат',
    )
    code_marketplace = models.ForeignKey(
        CodingMarketplaces,
        verbose_name='Код маркетплейса',
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = 'Продажи'
        verbose_name_plural = 'Продажи'


class Stocks_wb_frontend(models.Model):
    pub_date = models.DateField(
        verbose_name='Дата',
        auto_now_add=True
    )
    seller_article_wb = models.CharField(
        verbose_name='Артикул продавца на WB',
        max_length=50,
        null=True
    )
    article_wb = models.CharField(
        verbose_name='Артикул WB',
        max_length=50,
    )
    stock_name = models.CharField(
        verbose_name='Название склада WB',
        max_length=100,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Остатки на складах WB c фронтенда'
        verbose_name_plural = 'Остатки на складах WB c фронтенда'


class OrdersFbsInfo(models.Model):
    pub_date = models.DateField(
        verbose_name='Дата',
    )
    article_marketplace = models.CharField(
        verbose_name='Артикул маркетплейса',
        max_length=50,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
    )
    nomenclature_id = models.CharField(
        verbose_name='Номенклатура WB',
        max_length=50,
    )
    rid = models.CharField(
        verbose_name='rid',
        max_length=50,
    )

    class Meta:
        verbose_name = 'Заказы со склада FBS'
        verbose_name_plural = 'Заказы со склада FBS'


class WildberriesSales(models.Model):
    """Продажи Wildberries со всех юр. лиц"""
    date = models.DateTimeField(
        verbose_name='Дата и время продажи',
        blank=True,
        null=True
    )
    last_change_date = models.DateTimeField(
        verbose_name='Дата и время обновления информации в сервисе',
        blank=True,
        null=True
    )
    warehouse_name = models.CharField(
        verbose_name='Склад отгрузки',
        max_length=50,
        null=True,
        blank=True
    )
    country_name = models.CharField(
        verbose_name='Страна',
        max_length=200,
        null=True,
        blank=True
    )
    oblast_okrug_name = models.CharField(
        verbose_name='Округ',
        max_length=200,
        null=True,
        blank=True
    )
    region_name = models.CharField(
        verbose_name='Регион',
        max_length=200,
        null=True,
        blank=True
    )
    supplier_article = models.CharField(
        verbose_name='Артикул продавца',
        max_length=75,
        null=True,
        blank=True
    )
    nm_id = models.IntegerField(
        verbose_name='Артикул WB',
        null=True,
        blank=True
    )
    barcode = models.CharField(
        verbose_name='Баркод',
        max_length=30,
        null=True,
        blank=True
    )
    category = models.CharField(
        verbose_name='Категория',
        max_length=50,
        null=True,
        blank=True
    )
    subject = models.CharField(
        verbose_name='Предмет',
        max_length=50,
        null=True,
        blank=True
    )
    brand = models.CharField(
        verbose_name='Бренд',
        max_length=50,
        null=True,
        blank=True
    )
    tech_size = models.CharField(
        verbose_name='Размер товара',
        max_length=30,
        null=True,
        blank=True
    )
    income_id = models.IntegerField(
        verbose_name='Номер поставки',
        null=True,
        blank=True
    )
    is_supply = models.BooleanField(
        verbose_name='Договор поставки',
        null=True,
        blank=True
    )
    is_realization = models.BooleanField(
        verbose_name='Договор реализации',
        null=True,
        blank=True
    )
    total_price = models.FloatField(
        verbose_name='Цена без скидки',
        null=True,
        blank=True
    )
    discount_percent = models.IntegerField(
        verbose_name='Скидка продавца',
        null=True,
        blank=True
    )
    spp = models.FloatField(
        verbose_name='СПП',
        null=True,
        blank=True
    )
    payment_sale_amount = models.IntegerField(
        verbose_name='Оплачено с WB кошелька',
        null=True,
        blank=True
    )
    for_pay = models.FloatField(
        verbose_name='К перечислению продавцу',
        null=True,
        blank=True
    )

    finished_price = models.FloatField(
        verbose_name='Фактическая цена с учетом всех скидок (к взиманию с покупателя)',
        null=True,
        blank=True
    )
    price_with_disc = models.FloatField(
        verbose_name='Цена со скидкой продавца, от которой считается сумма к перечислению продавцу',
        null=True,
        blank=True
    )
    sale_id = models.CharField(
        verbose_name='Уникальный идентификатор продажи/возврата',
        max_length=15,
        null=True,
        blank=True
    )
    order_type = models.CharField(
        verbose_name='Тип заказа',
        max_length=75,
        null=True,
        blank=True
    )
    sticker = models.CharField(
        verbose_name='Идентификатор стикера',
        max_length=75,
        null=True,
        blank=True
    )
    g_number = models.CharField(
        verbose_name='Номер заказа',
        max_length=50,
        null=True,
        blank=True
    )
    srid = models.CharField(
        verbose_name='Уникальный идентификатор заказа.',
        max_length=75,
        null=True,
        blank=True
    )
    ur_lico = models.CharField(
        verbose_name='Юр. лицо',
        max_length=75,
        null=True,
        blank=True
    )
    month = models.IntegerField(
        verbose_name='Месяц',
        null=True,
        blank=True
    )
    year = models.IntegerField(
        verbose_name='год',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Продажи WB'
        verbose_name_plural = 'Продажи WB'


class OzonSales(models.Model):
    """Продажи Ozon со всех юр. лиц"""
    start_date_period = models.DateTimeField(
        verbose_name='Дата начала отчета продажи',
        blank=True,
        null=True
    )
    finish_date_period = models.DateTimeField(
        verbose_name='Дата окончания отчета продажи',
        blank=True,
        null=True
    )
    month = models.IntegerField(
        verbose_name='Месяц',
        null=True,
        blank=True
    )
    year = models.IntegerField(
        verbose_name='год',
        null=True,
        blank=True
    )
    number_report = models.CharField(
        verbose_name='номер отчета',
        max_length=75,
        null=True,
        blank=True
    )
    row_number = models.IntegerField(
        verbose_name='Номер строки в отчете',
        null=True,
        blank=True
    )
    offer_id = models.CharField(
        verbose_name='Артикул продавца',
        max_length=75,
        null=True,
        blank=True
    )
    sku = models.BigIntegerField(
        verbose_name='SKU товара',
        null=True,
        blank=True
    )
    barcode = models.CharField(
        verbose_name='Штрихкод товара',
        max_length=30,
        null=True,
        blank=True
    )
    name = models.CharField(
        verbose_name='Наименование товара',
        max_length=300,
        null=True,
        blank=True
    )
    seller_price_per_instance = models.FloatField(
        verbose_name='Цена продавца с учётом скидки',
        null=True,
        blank=True
    )
    amount = models.FloatField(
        verbose_name='Сумма',
        null=True,
        blank=True
    )
    bonus = models.FloatField(
        verbose_name='Баллы за скидки',
        null=True,
        blank=True
    )
    commission = models.FloatField(
        verbose_name='Итого комиссия с учётом скидок и наценки',
        null=True,
        blank=True
    )
    compensation = models.FloatField(
        verbose_name='Доплата за счёт Ozon',
        null=True,
        blank=True
    )
    price_per_instance = models.FloatField(
        verbose_name='Цена за экземпляр',
        null=True,
        blank=True
    )
    quantity = models.IntegerField(
        verbose_name='Количество товара',
        null=True,
        blank=True
    )
    standard_fee = models.FloatField(
        verbose_name='Базовое вознаграждение Ozon',
        null=True,
        blank=True
    )
    stars = models.FloatField(
        verbose_name='Выплаты по механикам лояльности партнёров',
        null=True,
        blank=True
    )
    total = models.FloatField(
        verbose_name='Итого к начислению',
        null=True,
        blank=True
    )
    return_amount = models.FloatField(
        verbose_name='Сумма',
        null=True,
        blank=True
    )
    return_bonus = models.FloatField(
        verbose_name='Баллы за скидки',
        null=True,
        blank=True
    )
    return_commission = models.FloatField(
        verbose_name='Итого комиссия с учётом скидок и наценки',
        null=True,
        blank=True
    )
    return_compensation = models.FloatField(
        verbose_name='Доплата за счёт Ozon',
        null=True,
        blank=True
    )
    return_price_per_instance = models.FloatField(
        verbose_name='Цена за экземпляр',
        null=True,
        blank=True
    )
    return_quantity = models.IntegerField(
        verbose_name='Количество товара',
        null=True,
        blank=True
    )
    return_standard_fee = models.FloatField(
        verbose_name='Базовое вознаграждение Ozon',
        null=True,
        blank=True
    )
    return_stars = models.FloatField(
        verbose_name='Выплаты по механикам лояльности партнёров',
        null=True,
        blank=True
    )
    return_total = models.FloatField(
        verbose_name='Итого к начислению',
        null=True,
        blank=True
    )
    commission_ratio = models.FloatField(
        verbose_name='Доля комиссии за продажу по категории',
        null=True,
        blank=True
    )
    ur_lico = models.CharField(
        verbose_name='Юр. лицо',
        max_length=75,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Продажи Ozon'
        verbose_name_plural = 'Продажи Ozon'


class OzonMonthlySalesData(models.Model):
    """Продажи Ozon по месяцам для всех юр. лиц"""
    start_date_period = models.DateTimeField(
        verbose_name='Дата начала отчета продажи',
        blank=True,
        null=True
    )
    finish_date_period = models.DateTimeField(
        verbose_name='Дата окончания отчета продажи',
        blank=True,
        null=True
    )
    number_report = models.CharField(
        verbose_name='Номер отчёта о реализации',
        max_length=75,
        null=True,
        blank=True
    )
    doc_date = models.DateTimeField(
        verbose_name='Дата формирования документа',
        blank=True,
        null=True
    )
    doc_amount = models.FloatField(
        verbose_name='Всего к начислению',
        null=True,
        blank=True
    )
    vat_amount = models.FloatField(
        verbose_name='Итоговая сумма с НДС',
        null=True,
        blank=True
    )
    month = models.IntegerField(
        verbose_name='Месяц',
        null=True,
        blank=True
    )
    year = models.IntegerField(
        verbose_name='год',
        null=True,
        blank=True
    )
    ur_lico = models.CharField(
        verbose_name='Юр. лицо',
        max_length=75,
        null=True,
        blank=True
    )


class OzonDailyOrders(models.Model):
    """Заказы артикулов Ozon со всех юр. лиц. Ежедневные данные"""
    order_date_period = models.DateTimeField(
        verbose_name='Дата заказа',
        blank=True,
        null=True
    )
    month = models.IntegerField(
        verbose_name='Месяц',
        null=True,
        blank=True
    )
    year = models.IntegerField(
        verbose_name='год',
        null=True,
        blank=True
    )
    ozon_sku = models.BigIntegerField(
        verbose_name='SKU товара',
        null=True,
        blank=True
    )
    amount = models.IntegerField(
        verbose_name='Количество',
        null=True,
        blank=True
    )
    order_summ = models.IntegerField(
        verbose_name='Сумма заказов за день',
        null=True,
        blank=True
    )
    ur_lico = models.CharField(
        verbose_name='Юр. лицо',
        max_length=75,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Ежедневные заказы Ozon'
        verbose_name_plural = 'Ежедневные заказы Ozon'


class YandexSales(models.Model):
    """Продажи Ozon со всех юр. лиц"""
