from datetime import datetime

from django.db import models
from django.urls import reverse


class Articles(models.Model):
    common_article = models.CharField(
        verbose_name='Артикул',
        max_length=50,
        unique=True,
        null=True
    )
    status = models.CharField(
        verbose_name='Статус',
        max_length=30,
        blank=True,
        null=True
    )
    company = models.CharField(
        verbose_name='Юр. лицо',
        max_length=30,
        blank=True,
        null=True
    )
    wb_seller_article = models.CharField(
        verbose_name='WB арт пост',
        max_length=50,
        blank=True,
        null=True,
    )
    wb_barcode = models.PositiveBigIntegerField(
        verbose_name='WB баркод',
        blank=True,
        null=True,
    )
    wb_nomenclature = models.PositiveBigIntegerField(
        verbose_name='WB номенк',
        blank=True,
        null=True,
    )
    ozon_seller_article = models.CharField(
        verbose_name='OZON арт пост',
        max_length=50,
        blank=True,
        null=True,
    )
    ozon_barcode = models.PositiveBigIntegerField(
        verbose_name='OZON баркод',
        blank=True,
        null=True,
    )
    ozon_product_id = models.PositiveBigIntegerField(
        verbose_name='OZON Product ID',
        blank=True,
        null=True,
    )
    ozon_sku = models.PositiveBigIntegerField(
        verbose_name='OZON SKU',
        blank=True,
        null=True,
    )
    ozon_fbo_sku_id = models.PositiveBigIntegerField(
        verbose_name='OZON FBO SKU ID',
        blank=True,
        null=True,
    )
    ozon_fbs_sku_id = models.PositiveBigIntegerField(
        verbose_name='OZON FBS SKU ID',
        blank=True,
        null=True,
    )

    yandex_seller_article = models.CharField(
        verbose_name='YANDEX арт пост',
        max_length=50,
        blank=True,
        null=True,
    )
    yandex_barcode = models.PositiveBigIntegerField(
        verbose_name='YANDEX баркод',
        blank=True,
        null=True,
    )
    yandex_sku = models.PositiveBigIntegerField(
        verbose_name='YANDEX SKU',
        blank=True,
        null=True,
    )
    multiplicity = models.PositiveSmallIntegerField(
        verbose_name='Кратность',
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.common_article

    class Meta:
        verbose_name = 'Таблица сверки'
        verbose_name_plural = 'Таблица сверки'


class Groups(models.Model):
    name = models.CharField(
        verbose_name='Артикул',
        max_length=50,
        blank=True,
        null=True
    )
    wb_price = models.IntegerField(
        verbose_name='WB стоимость',
        blank=True,
        null=True
    )
    ozon_price = models.IntegerField(
        verbose_name='OZON стоимость',
        blank=True,
        null=True
    )
    yandex_price = models.IntegerField(
        verbose_name='YANDEX стоимость',
        blank=True,
        null=True
    )
    min_price = models.IntegerField(
        verbose_name='Минимальная цена',
        blank=True,
        null=True
    )
    old_price = models.IntegerField(
        verbose_name='Старая цена',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Ценовые группы'
        verbose_name_plural = 'Ценовые группы'


class ArticleGroup(models.Model):
    common_article = models.ForeignKey(
        Articles,
        verbose_name='Общий артикул',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    group = models.ForeignKey(
        Groups,
        verbose_name='Ценовая группа',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Соответствие артикул - группа'
        verbose_name_plural = 'Соответствие артикул - группа'


class ArticlesPrice(models.Model):
    """Модель фиксирует изменение цен на артикул"""
    common_article = models.ForeignKey(
        Articles,
        verbose_name='Общий артикул',
        related_name='articleprice',
        on_delete=models.CASCADE,
        null=True
    )
    marketplace = models.CharField(
        verbose_name='Маркетплейс',
        max_length=15,
        blank=True,
        null=True
    )
    price_date = models.DateTimeField(
        verbose_name='Дата изменения цены',
        blank=True,
        null=True
    )
    basic_discount = models.IntegerField(
        verbose_name='Скидка продавца',
        blank=True,
        null=True
    )
    spp = models.IntegerField(
        verbose_name='Скидка постоянного покупателя',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Изменение цен на артикул'
        verbose_name_plural = 'Изменение цен на артикул'
