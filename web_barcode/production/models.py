from datetime import datetime
from django.db.models import Sum
from django.db import models
from django.urls import reverse


class ArticlesDelivery(models.Model):
    """Модель описывает артикулы и их количество, которое нужно произвести"""
    subject = models.CharField(
        verbose_name='Предмет',
        max_length=250,
    )
    supplier_article = models.CharField(
        verbose_name='Артикул поставщика',
        max_length=100,
    )
    from_stock = models.PositiveSmallIntegerField(
        verbose_name='Со склада',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Артикулы поставки'
        verbose_name_plural = 'Артикулы поставки'


class ProductionDelivery(models.Model):
    """Модель описывает ежедневное производство артикулов"""
    articles = models.ForeignKey(ArticlesDelivery, on_delete=models.CASCADE)
    
    fact_amount = models.CharField(
        verbose_name='Количество',
        max_length=50,
        blank=True,
        null=True,
    )
    production_date = models.DateField(
        verbose_name='Дата производства',
    )
    day_quantity = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='День',
    )
    night_quantity =  models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Ночь',

    )
    
    @property

    def total_production(self):
        total = 0
        productions = ProductionDelivery.objects.filter(articles=self.articles)
        for production in productions:
            total += production.day_quantity + production.night_quantity
        amount = total + self.articles.from_stock
        return amount

    
    def __str__(self):
        return self.articles.supplier_article

    class Meta:
        verbose_name = 'Производство артикулов'
        verbose_name_plural = 'Производство артикулов'


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
    fact_amount = models.CharField(
        verbose_name='Количество',
        max_length=50,
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

    @property
    def produced(self):
        
        if self.day_production_amount and self.night_production_amount:
            return Delivery.objects.aggregate(total=Sum(self.day_production_amount)+Sum(self.night_production_amount))['total']
        elif self.day_production_amount :
            return Delivery.objects.aggregate(total=Sum(self.day_production_amount))['total']
        elif self.night_production_amount :
            return Delivery.objects.aggregate(total=Sum(self.night_production_amount))['total']
        else:
            return 0

    def __str__(self):
        return self.supplier_article

    class Meta:
        verbose_name = 'Поставка'
        verbose_name_plural = 'Поставка'
