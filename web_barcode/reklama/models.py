from datetime import datetime

from django.db import models
from django.urls import reverse


class UrLico(models.Model):
    ur_lice_name = models.CharField(
        verbose_name='Юр. лицо'
    )

    def __str__(self):
        return self.ur_lice_name

    class Meta:
        verbose_name = 'Юр. лицо'
        verbose_name_plural = 'Юр. лицо'


class AdvertisingCampaign(models.Model):
    campaign_number = models.CharField(
        verbose_name='Рекламная компания ВБ',
        max_length=20
    )
    ur_lico = models.ForeignKey(
        UrLico,
        on_delete=models.CASCADE,
        verbose_name='Юр. лицо',
        related_name='ad_campaign'
    )
    create_date = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )

    def __str__(self):
        return self.campaign_number

    class Meta:
        verbose_name = 'Рекламная кампания ВБ'
        verbose_name_plural = 'Рекламная кампания ВБ'


class ProcentForAd(models.Model):
    campaign_number = models.ForeignKey(
        AdvertisingCampaign,
        on_delete=models.CASCADE,
        verbose_name='Рекламная кампания',
        related_name='procentforad'
    )
    koefficient = models.IntegerField(
        verbose_name='Процент для рекламы',
    )
    koef_date = models.DateTimeField(
        verbose_name='Дата коэффициента',
        auto_now_add=True
    )
    virtual_budget = models.IntegerField(
        verbose_name='Виртуальный бюджет',
        default=0
    )

    def __str__(self):
        return self.campaign_number.campaign_number, self.koefficient

    class Meta:
        verbose_name = 'Коэффициент для кампании'
        verbose_name_plural = 'Коэффициент для кампании'


class CompanyStatistic(models.Model):
    campaign_number = models.ForeignKey(
        AdvertisingCampaign,
        on_delete=models.CASCADE,
        verbose_name='Рекламная компания',
        related_name='companystatistic'
    )
    date = models.DateTimeField(
        verbose_name='Дата',
        auto_now_add=True
    )
    sales_per_money = models.FloatField(
        verbose_name='Продажи в рублях',
        blank=True,
        null=True
    )
    sales_per_amount = models.FloatField(
        verbose_name='Продажи в штуках',
        blank=True,
        null=True
    )
    cost_for_ad = models.FloatField(
        verbose_name='Затраты на рекламу',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.campaign_number

    class Meta:
        verbose_name = 'Статистика кампании'
        verbose_name_plural = 'Статистика кампании'


class WbArticleCommon(models.Model):
    wb_article = models.BigIntegerField(
        verbose_name='Артикул WB',
    )

    def __str__(self):
        return self.wb_article

    class Meta:
        verbose_name = 'Артикул WB'
        verbose_name_plural = 'Артикул WB'


class WbArticleCompany(models.Model):
    campaign_number = models.ForeignKey(
        AdvertisingCampaign,
        on_delete=models.CASCADE,
        verbose_name='Рекламная компания',
        related_name='wbarticle_company'
    )
    wb_article = models.ForeignKey(
        WbArticleCommon,
        on_delete=models.CASCADE,
        verbose_name='Артикул WB',
        related_name='wbarticle_company'
    )

    def __str__(self):
        return self.wb_article

    class Meta:
        verbose_name = 'Артикул компании'
        verbose_name_plural = 'Артикул компании'


class SalesArticleStatistic(models.Model):
    campaign_number = models.ForeignKey(
        AdvertisingCampaign,
        on_delete=models.CASCADE,
        verbose_name='Рекламная компания',
        related_name='article_statistic'
    )
    wb_article = models.ForeignKey(
        WbArticleCompany,
        on_delete=models.CASCADE,
        verbose_name='Артикул WB',
        related_name='article_statistic'
    )
    date = models.DateTimeField(
        verbose_name='Дата',
        auto_now_add=True
    )
    sales_per_money = models.FloatField(
        verbose_name='Продажи в рублях',
        blank=True,
        null=True
    )
    sales_per_amount = models.FloatField(
        verbose_name='Продажи в штуках',
        blank=True,
        null=True
    )
    cost_for_ad = models.FloatField(
        verbose_name='Затраты на рекламу',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.campaign_number.wb_article

    class Meta:
        verbose_name = 'Статистика артикула на ВБ'
        verbose_name_plural = 'Статистика артикула на ВБ'


class OzonCampaign(models.Model):
    """Модель для рекламной кампании ОЗОН"""
    campaign_number = models.CharField(
        verbose_name='Рекламная компания ОЗОН',
        max_length=20
    )
    ur_lico = models.ForeignKey(
        UrLico,
        on_delete=models.CASCADE,
        verbose_name='Юр. лицо',
        related_name='ozon_ad_campaign'
    )
    status = models.CharField(
        verbose_name='Статус кампании',
        max_length=50,
        blank=True,
        null=True
    )
    article_amount = models.IntegerField(
        verbose_name='Количество артикулов',
        blank=True,
        null=True
    )
    create_date = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )

    def __str__(self):
        return self.campaign_number

    class Meta:
        verbose_name = 'Рекламная кампания ОЗОН'
        verbose_name_plural = 'Рекламная кампания ОЗОН'


class OooWbArticle(models.Model):
    """Список артикулов ООО с Wildberries. Пока что без сопоставления"""
    wb_article = models.CharField(
        verbose_name='Артикул ООО ВБ',
        max_length=50,
        unique=True
    )
    wb_nomenclature = models.IntegerField(
        verbose_name='Номенклатура ООО ВБ',
        blank=True,
        null=True
    )
    article_title = models.CharField(
        verbose_name='Название артикула',
        max_length=300,
        blank=True,
        null=True
    )

    # def __str__(self):
    #     return str(self.pk)

    class Meta:
        verbose_name = 'Артикул ВБ ООО'
        verbose_name_plural = 'Артикул ВБ ООО'


class DataOooWbArticle(models.Model):
    """Содержит информацию артикулов ООО с Wildberries."""
    wb_article = models.ForeignKey(
        OooWbArticle,
        verbose_name='Артикул ООО ВБ',
        on_delete=models.CASCADE,
        related_name='data_wb_article',
    )
    fbo_amount = models.IntegerField(
        verbose_name='Остаток на складе FBO',
        blank=True,
        null=True
    )
    ad_campaign = models.ForeignKey(
        AdvertisingCampaign,
        verbose_name='Кампания артикула',
        on_delete=models.CASCADE,
        related_name='data_wb_article',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Информация артикулов ВБ ООО'
        verbose_name_plural = 'Информация артикулов ВБ ООО'
