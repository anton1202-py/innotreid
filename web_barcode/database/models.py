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
        return self.seller_article

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

    def get_absolute_url(self): # new
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
