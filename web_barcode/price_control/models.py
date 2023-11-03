from django.db import models


class ArticleWriter(models.Model):
    """
    Модель с артикулами продавца и артикулами WB, которую дополняет
    пользователь на сайте. Сам вводит данные по артикулам
    """
    seller_article = models.CharField(
        verbose_name='Артикул продавца',
        max_length=100,
    )
    wb_article = models.CharField(
        verbose_name='Артикул Wildberries',
        max_length=100,
    )

    def __str__(self):
        return self.seller_article

    class Meta:
        verbose_name = 'Артикулы для анализа'
        verbose_name_plural = 'Артикулы для анализа'


class DataForAnalysis(models.Model):
    """
    Модель с данными для анализа цен по каждому артикулу из таблицы ArticleWriter.
    Таблица заполняется функцией (ЗАПИСАТЬ ФУНКЦИЮ), которую включает celery раз в сутки.
    """
    seller_article = models.CharField(
        verbose_name='Артикул продавца',
        max_length=100,
    )
    wb_article = models.CharField(
        verbose_name='Артикул Wildberries',
        max_length=100,
    )
    price_date = models.DateTimeField(
        verbose_name='Дата',
    )
    price = models.PositiveSmallIntegerField(
        verbose_name='Цена',
    )
    spp = models.CharField(
        verbose_name='Скидка постоянного покупателя',
        max_length=30,
    )
    basic_sale = models.CharField(
        verbose_name='Базовая скидка',
        max_length=30,
    )

    class Meta:
        verbose_name = 'Данные для анализа цен'
        verbose_name_plural = 'Данные для анализа цен'
