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

    yandex_article_seller = models.CharField(
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
