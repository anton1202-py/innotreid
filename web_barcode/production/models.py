from datetime import datetime
from decimal import Decimal

from database.models import CodingMarketplaces
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q, Sum
from django.urls import reverse

PERCENTAGE_VALIDATOR = [MinValueValidator(0), MaxValueValidator(100)]


class TaskCreator(models.Model):
    """Модель описывает создание задачи для производства"""
    task_name = models.CharField(
        verbose_name='Название задачи',
        max_length=100,
    )
    market_name = models.ForeignKey(
        CodingMarketplaces,
        verbose_name='Маркетплейс',
        on_delete=models.PROTECT,
    )
    plate_production = models.CharField(
        verbose_name='Изготовление пластин',
        max_length=50,
        blank = True,
        null=True,
    )
    progress = models.CharField(
        verbose_name='Прогресс',
        max_length=10)

    remainder = models.CharField(
        verbose_name='Остаток/Общее количество',
        blank = True,
        null=True,
        max_length=50,
    )
    stickers = models.CharField(
        verbose_name='Наклейки',
        blank = True,
        null=True,
        max_length=50,
    )
    printing = models.BooleanField(
        verbose_name='В печати',
        blank = True,
        null=True,
    )
    printed = models.BooleanField(
        verbose_name='Напечатаны',
        blank = True,
        null=True,
    )
    shipment_status = models.BooleanField(
        verbose_name='Статус отгрузки',
        blank = True,
        null=True,

    )
    shipping_date = models.DateField(
        verbose_name='Дата отгрузки',
        blank=True,
        null=True,
    )


class ArticlesDelivery(models.Model):
    """Модель описывает артикулы и их количество, которое нужно произвести"""
    task = models.ForeignKey(
        TaskCreator,
        default=1,
        verbose_name='Номер задания',
        on_delete=models.PROTECT,
    )
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

    @property
    def amount_delivery(self):
        amount_delivery = ArticlesDelivery.objects.filter(Q(task=self.task)).aggregate(
        total_amount=Sum('amount'))['total_amount']
        return amount_delivery

    class Meta:
        verbose_name = 'Артикулы поставки'
        verbose_name_plural = 'Артикулы поставки'


class ProductionDelivery(models.Model):
    """Модель описывает ежедневное производство артикулов"""
    task =  models.ForeignKey(TaskCreator, on_delete=models.CASCADE)
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
        productions = ProductionDelivery.objects.filter(Q(articles=self.articles))
        for production in productions:
            total += production.day_quantity + production.night_quantity
        amount = total + self.articles.from_stock
        return amount
    
    @property
    def total_delivery_production(self):
        production_delivery = ProductionDelivery.objects.filter(Q(task=self.task)).aggregate(
        total_sum=Sum('day_quantity') + Sum('night_quantity')
        )['total_sum']
        total_delivery = production_delivery + self.articles.from_stock
        return total_delivery


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
