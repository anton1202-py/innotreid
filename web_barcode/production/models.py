from datetime import datetime

from django.db import models
from django.urls import reverse


class Delivery(models.Model):
    subject = models.CharField(
        verbose_name='Предмет',
        max_length=250,
        blank=True,
        null=True,
    )
    supplier_article = models.CharField(
        verbose_name='Артикул поставщика',
        max_length=100,
        blank=True,
        null=True,
    )
    from_stock = models.PositiveSmallIntegerField(
        verbose_name='Со склада',
        blank=True,
        null=True,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        blank=True,
        null=True,
    )
    production_date = models.DateField(
        verbose_name='Дата производства',
        blank=True,
        null=True,
    )
    day_production_amount = models.PositiveSmallIntegerField(
        verbose_name='День',
        blank=True,
        null=True,
    )
    night_production_amount = models.PositiveSmallIntegerField(
        verbose_name='Ночь',
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.supplier_article

    class Meta:
        verbose_name = 'Поставка'
        verbose_name_plural = 'Поставка'
