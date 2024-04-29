from database.models import CodingMarketplaces
from django.contrib.auth.models import User
from django.db import models
from price_system.models import Articles


class DesignUser(models.Model):
    designer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Дизайнер',
        related_name='designer'
    )
    tg_chat_id = models.PositiveBigIntegerField(
        verbose_name='chat_id телеграма',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.designer.last_name

    class Meta:
        verbose_name = 'Дизайнеры'
        verbose_name_plural = 'Дизайнеры'


class Lighters(models.Model):
    article = models.ForeignKey(
        Articles,
        on_delete=models.CASCADE,
        verbose_name='Светильник',
        related_name='lighter'
    )
    designer = models.ForeignKey(
        DesignUser,
        on_delete=models.CASCADE,
        verbose_name='Дизайнер',
        related_name='lighter_designer',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Светильники дизайнеров'
        verbose_name_plural = 'Светильники дизайнеров'


class Selling(models.Model):
    lighter = models.ForeignKey(
        Lighters,
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
        on_delete=models.PROTECT,
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
