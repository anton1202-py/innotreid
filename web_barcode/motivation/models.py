from database.models import CodingMarketplaces
from django.db import models
from price_system.models import Articles, DesignUser


class Selling(models.Model):
    lighter = models.ForeignKey(
        Articles,
        on_delete=models.CASCADE,
        verbose_name='Светильник',
        related_name='lighter'
    )
    data = models.DateTimeField(
        verbose_name='Дата создания',
        null=True,
        blank=True
    )
    marketplace = models.ForeignKey(
        CodingMarketplaces,
        verbose_name='Маркетплейс',
        on_delete=models.CASCADE,
    )
    quantity = models.IntegerField(
        verbose_name='Количество',
        null=True,
        blank=True
    )
    summ = models.FloatField(
        verbose_name='Сумма',
        null=True,
        blank=True
    )
    month = models.IntegerField(
        verbose_name='Месяц',
        null=True,
        blank=True
    )
    year = models.IntegerField(
        verbose_name='год',
        null=True,
        blank=True
    )
    ur_lico = models.CharField(
        verbose_name='Юр. лицо',
        max_length=75,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Продажи светильников'
        verbose_name_plural = 'Продажи светильников'


class DesignerReward(models.Model):
    designer = models.ForeignKey(
        DesignUser,
        on_delete=models.CASCADE,
        verbose_name='Дизайнер',
        related_name='reward_designer'
    )
    data = models.DateTimeField(
        verbose_name='Дата',
        null=True,
        blank=True
    )
    reward = models.FloatField(
        verbose_name='Вознаграждение',
        null=True,
        blank=True
    )
    article_amount = models.IntegerField(
        verbose_name='Количество артикулов',
        null=True,
        blank=True
    )
    virtual_balance = models.FloatField(
        verbose_name='Виртуальный счет',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Вознаграждение дизайнеров'
        verbose_name_plural = 'Вознаграждение дизайнеров'
