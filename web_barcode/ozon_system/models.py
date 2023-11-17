from django.db import models


class ArticleAmountRating(models.Model):
    """Модель, которая хранит данных об артикулах и их группах"""
    seller_article = models.CharField(
        verbose_name='Артикул Продавца',
        max_length=150,
        blank=True,
        null=True,
    )
    sku = models.CharField(
        verbose_name='SKU',
        max_length=30,
        blank=True,
        null=True,
    )
    sale_amount = models.IntegerField(
        verbose_name='Количество проданных товаров',
        blank=True,
        null=True,)
    sale_summa = models.FloatField(
        verbose_name='Сумма проданных товаров',
        blank=True,
        null=True,)
    article_group = models.PositiveSmallIntegerField(
        verbose_name='Группа артикула',
        blank=True,
        null=True,
    )


class DateActionInfo(models.Model):
    """Модель, показывает данные о начале запуска действия с группой"""
    company_number = models.CharField(
        verbose_name='ID компании',
        blank=True,
        null=True,
    )
    action_type = models.CharField(
        verbose_name='Действие',
        blank=True,
        null=True,
    )
    start_task_datetime = models.DateTimeField(
        verbose_name='Дата и время постановки задачи',
        auto_now_add=True,
    )
    action_datetime = models.DateTimeField(
        verbose_name='Дата и время действия',
        blank=True,
        null=True,
    )
    celery_task = models.CharField(
        verbose_name='ID задачи celery',
        blank=True,
        null=True,
    )
