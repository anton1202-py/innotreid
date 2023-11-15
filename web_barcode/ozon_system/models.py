from django.db import models


class ArticleAmountRating(models.Model):
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
