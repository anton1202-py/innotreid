from datetime import datetime

from django.db import models
from django.urls import reverse
from database.models import CodingMarketplaces


class Stocks_Innotreid(models.Model):
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
        verbose_name = 'Склад ООО Иннотрейд'
        verbose_name_plural = 'Склад ООО Иннотрейд'
