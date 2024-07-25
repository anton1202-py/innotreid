from datetime import datetime

from django.db import models
from django.urls import reverse
from price_system.models import Articles
from reklama.models import UrLico


class CreatedCampaign(models.Model):
    """Описывает созданную через интерфейс системы рекламную кампанию"""
    campaign_number = models.CharField(
        verbose_name='ID рекламной кампании ВБ',
        max_length=30
    )
    campaign_name = models.CharField(
        verbose_name='Название рекламной кампании ВБ',
        max_length=300
    )
    ur_lico = models.ForeignKey(
        UrLico,
        on_delete=models.CASCADE,
        verbose_name='Юр. лицо',
        related_name='created_campaign'
    )
    campaign_type = models.SmallIntegerField(
        verbose_name='Тип рекламной кампании',
    )
    campaign_status = models.SmallIntegerField(
        verbose_name='Статус рекламной кампании',
    )
    create_date = models.DateTimeField(
        verbose_name='Дата создания',
        blank=True,
        null=True
    )
    pausa_date = models.DateTimeField(
        verbose_name='Дата остановки кампании',
        blank=True,
        null=True
    )
    start_date = models.DateTimeField(
        verbose_name='Дата запуска кампании',
        blank=True,
        null=True
    )
    articles_name = models.JSONField(
        verbose_name='Список артикулов nmID',
        blank=True,
        null=True
    )
    article_price_on_page = models.IntegerField(
        verbose_name='Цена артикула на странице',
        blank=True,
        null=True
    )
    subject_id = models.IntegerField(
        verbose_name='ID предмета, для которого создается кампания.',
        blank=True,
        null=True
    )
    current_cpm = models.IntegerField(
        verbose_name='Текущая ставка',
        blank=True,
        null=True
    )
    balance = models.IntegerField(
        verbose_name='Баланс кампании',
        blank=True,
        null=True
    )

    def __str__(self):
        return f'{self.campaign_number} {self.campaign_name}'

    class Meta:
        verbose_name = 'Созданная рекламная кампании ВБ'
        verbose_name_plural = 'Созданная рекламная кампании ВБ'


class ReplenishWbCampaign(models.Model):
    """История пополнения рекламной кампании ВБ"""
    campaign_number = models.ForeignKey(
        CreatedCampaign,
        on_delete=models.SET_NULL,
        verbose_name='Рекламная кампания',
        related_name='replenish_campaign',
        blank=True,
        null=True
    )

    sum = models.IntegerField(
        verbose_name='Сумма пополнения РК',
        blank=True,
        null=True
    )
    replenish_date = models.DateTimeField(
        verbose_name='Дата пополнения',
        blank=True,
        null=True
    )

    def __str__(self):
        return f'{self.campaign_number.campaign_name}'

    class Meta:
        verbose_name = 'Пополнение рекламной кампании ВБ'
        verbose_name_plural = 'Пополнение рекламной кампании ВБ'


class CpmWbCampaign(models.Model):
    """История изменения ставки рекламной кампании ВБ"""
    campaign_number = models.ForeignKey(
        CreatedCampaign,
        on_delete=models.SET_NULL,
        verbose_name='Рекламная кампания',
        related_name='cpm_wb_campaign',
        blank=True,
        null=True
    )

    cpm = models.IntegerField(
        verbose_name='Ставка РК',
        blank=True,
        null=True
    )
    cpm_date = models.DateTimeField(
        verbose_name='Дата изменения ставки',
        blank=True,
        null=True
    )

    def __str__(self):
        return f'{self.campaign_number.campaign_name}'

    class Meta:
        verbose_name = 'Изменение ставок кампании ВБ'
        verbose_name_plural = 'Изменение ставок рекламной кампании ВБ'


# ========= ПОПОЛНЕНИЕ РЕКЛАМНЫХ КАМПАНИЙ ========== #
class ProcentForAd(models.Model):
    """Процент от продаж для пополнения рекламной кампании"""
    campaign_number = models.ForeignKey(
        CreatedCampaign,
        on_delete=models.CASCADE,
        verbose_name='Рекламная кампания',
        related_name='procentforad'
    )
    koefficient = models.IntegerField(
        verbose_name='Процент для пополнения',
        default=4
    )
    koef_date = models.DateTimeField(
        verbose_name='Дата изменения процента',
        auto_now_add=True,
        blank=True,
        null=True
    )
    virtual_budget = models.IntegerField(
        verbose_name='Виртуальный счет',
        default=0
    )
    virtual_budget_date = models.DateTimeField(
        verbose_name='Дата изменения виртуального счета',
        blank=True,
        null=True
    )
    campaign_budget_date = models.DateTimeField(
        verbose_name='Дата пополнения счета РК',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.campaign_number.campaign_number, self.koefficient

    class Meta:
        verbose_name = 'Процент для поплнения кампании'
        verbose_name_plural = 'Процент для поплнения кампании'


class AutoReplenish(models.Model):
    """Автопополнение кампаний"""
    campaign_number = models.ForeignKey(
        CreatedCampaign,
        on_delete=models.SET_NULL,
        verbose_name='Рекламная кампания',
        related_name='auto_replenish',
        blank=True,
        null=True
    )
    auto_replenish = models.BooleanField(
        verbose_name='Автопополнение',
        default=False
    )
    auto_replenish_summ = models.IntegerField(
        verbose_name='Сумма автопополнения',
        default=0
    )

    def __str__(self):
        return self.campaign_number.campaign_number

    class Meta:
        verbose_name = 'Автопополнение кампаний'
        verbose_name_plural = 'Автопополнение кампаний'

# ========= КОНЕЦ ПОПОЛНЕНИЕ РЕКЛАМНЫХ КАМПАНИЙ ========== #


class MinusWordsWbCampaign(models.Model):
    """Минус слова рекламной кампании ВБ"""
    campaign_number = models.ForeignKey(
        CreatedCampaign,
        on_delete=models.SET_NULL,
        verbose_name='Рекламная кампания',
        related_name='minus_words_campaign',
        blank=True,
        null=True
    )

    word = models.CharField(
        verbose_name='Минус слово',
        max_length=300,
        blank=True,
        null=True
    )

    def __str__(self):
        return f'{self.campaign_number.campaign_name}'

    class Meta:
        verbose_name = 'Минус слова кампании ВБ'
        verbose_name_plural = 'Минус слова рекламной кампании ВБ'


class AllMinusWords(models.Model):
    """Минус слова я всех рекламных кампаний"""
    now_date = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
    word = models.CharField(
        verbose_name='Минус слово',
        max_length=300,
        blank=True,
        null=True
    )
    ur_lico = models.ForeignKey(
        UrLico,
        on_delete=models.SET_NULL,
        verbose_name='Юр. лицо',
        related_name='common_minus_words',
        blank=True,
        null=True
    )
    create_date = models.DateTimeField(
        verbose_name='Дата добавления',
        auto_now_add=True
    )

    def __str__(self):
        return f'{self.word}'

    class Meta:
        verbose_name = 'Минус слова для всех кампаний'
        verbose_name_plural = 'Минус слова для всех кампаний'


class SenderStatisticDaysAmount(models.Model):
    """Определяет за какое количество дней отрпавлять статитстику в рекламных кампаниях"""
    days_amount = models.IntegerField(
        verbose_name='Количество дней',
        default=0
    )

    def __str__(self):
        return self.days_amount

    class Meta:
        verbose_name = 'Количество дней для статистики'
        verbose_name_plural = 'Количество дней для статистики'
