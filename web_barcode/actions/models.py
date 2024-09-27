from django.db import models
from reklama.models import UrLico
from database.models import CodingMarketplaces
from price_system.models import Articles

class Action(models.Model):
    """Описывает акцию на маркетплейсе"""

    ur_lico = models.ForeignKey(UrLico, on_delete=models.SET_NULL,
        verbose_name='Юр. лицо', related_name='actions')
    marketplace = models.ForeignKey(CodingMarketplaces, on_delete=models.SET_NULL,
        verbose_name='Маркетплейс', related_name='actions')
    action_number = models.CharField(verbose_name='Номер акции', max_length=100)
    name = models.CharField(verbose_name='Название акции', max_length=255)
    description = models.TextField(verbose_name='Описание акции')
    date_start = models.DateTimeField(verbose_name='Дата начала акции')
    date_finish = models.DateTimeField(verbose_name='Дата завершения акции')
    action_type = models.CharField(verbose_name='Тип акции', max_length=100)
    articles_amount = models.IntegerField(verbose_name='Количество товаров, которые могут участвовать',
        null=True, blank=True)
    
    def __str__(self):
        return f'{self.action_number} {self.name}'

    class Meta:
        verbose_name = 'Акция на маркетплейсе'
        verbose_name_plural = 'Акция на маркетплейсе'


class ArticleMayBeInAction(models.Model):
    """Описывает артикул, который может участвовать в акции"""
    
    action = models.ForeignKey(Action, on_delete=models.CASCADE,
        verbose_name='Акция', related_name='maybe_in_action')
    article = models.ForeignKey(Articles, on_delete=models.CASCADE,
        verbose_name='Артикул', related_name='maybe_in_action')
    action_price = models.FloatField(verbose_name='Цена в акции',
        null=True, blank=True)
    action_discount = models.FloatField(verbose_name='Скидка в акции',
        null=True, blank=True)
    
    def __str__(self):
        return f'{self.article.common_article} {self.action.name}'

    class Meta:
        verbose_name = 'Артикул, который может участвовать в акции'
        verbose_name_plural = 'Артикул, который может участвовать в акции'


class ArticleInActionWithCondition(models.Model):
    """
    Модель описывает товар, который можно поместить в акции,
    так как соблюдаются условия
    """
    article = article = models.ForeignKey(Articles, on_delete=models.CASCADE,
        verbose_name='Артикул', related_name='action_condition')
    wb_action = models.ForeignKey(Action, on_delete=models.CASCADE,
        verbose_name='Акция на ВБ', related_name='wb_maybe_in_action')
    ozon_action_id = models.ForeignKey(Action, on_delete=models.CASCADE,
        verbose_name='Акция на Озон', related_name='ozon_maybe_in_action')
    go_to_action = models.BooleanField(verbose_name='Может участвовать в акции ВБ')
    reason_for_refusal = models.TextField(verbose_name='Причина отказа, если не может',
        null=True, blank=True)
    
    def __str__(self):
        return f'{self.article.common_article} {self.wb_action.name}'

    class Meta:
        verbose_name = 'Артикул, который можно поместить в акции, так как соблюдаются условия'
        verbose_name_plural = 'Артикул, который можно поместить в акции, так как соблюдаются условия'


class ArticleInAction(models.Model):
    """Товар в акции"""
    article = article = models.ForeignKey(Articles, on_delete=models.CASCADE,
        verbose_name='Артикул', related_name='in_action')
    action = models.ForeignKey(Action, on_delete=models.SET_NULL,
        verbose_name='Акция', related_name='in_action')
    date_start = models.DateTimeField(verbose_name='Дата захода в акцию')
    date_finish = models.DateTimeField(verbose_name='Дата выхода из акции')

    def __str__(self):
        return f'{self.article.common_article} {self.action.name}'

    class Meta:
        verbose_name = 'Товар в акции'
        verbose_name_plural = 'Товар в акции'