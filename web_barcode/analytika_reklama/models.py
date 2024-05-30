from django.db import models
from django.urls import reverse
from reklama.models import UrLico


class CommonCampaignDescription(models.Model):
    """
    Общее описание рекламной кампании на ВБ.

    Описание типов кампании:
    4 - в каталоге
    5 - в карточке товара
    6 - в поиске
    7 - в рекомендациях на главной странице
    8 - автоматическая
    9 - поиск + каталог

    Описание статусов кампаний
    -1 - в процессе удаления
    4 - готова к запуску
    7 - завершена
    8 - отказался
    9 - идут показы
    11 - на паузе

    """
    campaign_number = models.CharField(
        verbose_name='ID рекламной кампании ВБ',
        max_length=20
    )

    campaign_name = models.CharField(
        verbose_name='Название рекламной кампании ВБ',
        max_length=20
    )
    ur_lico = models.ForeignKey(
        UrLico,
        on_delete=models.CASCADE,
        verbose_name='Юр. лицо',
        related_name='com_desc_campaign'
    )
    camnpaign_type = models.SmallIntegerField(
        verbose_name='Тип рекламной кампании',
    )
    camnpaign_status = models.SmallIntegerField(
        verbose_name='Статус рекламной кампании',
    )
    create_date = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )

    def __str__(self):
        return f'{self.campaign_number} {self.campaign_name}'

    class Meta:
        verbose_name = 'Общее описание рекламной кампании ВБ'
        verbose_name_plural = 'Общее описание рекламной кампании ВБ'


class MainCampaignParameters(models.Model):
    """
    Общие параметры рекламной кампании ВБ
    """
    campaign = models.ForeignKey(
        CommonCampaignDescription,
        on_delete=models.CASCADE,
        verbose_name='Рекламная кампания',
        related_name='main_par_campaign'
    )
    articles_amount = models.SmallIntegerField(
        verbose_name='Количество артикулов',
        blank=True,
        null=True
    )
    articles_name = models.CharField(
        verbose_name='Названия артикулов',
        max_length=500,
        blank=True,
        null=True
    )
    clasters_list = models.TextField(
        verbose_name='Список кластеров кампании',
        blank=True,
        null=True
    )
    views = models.IntegerField(
        verbose_name='Просмотры',
        blank=True,
        null=True
    )
    clicks = models.IntegerField(
        verbose_name='Клики',
        blank=True,
        null=True
    )
    ctr = models.FloatField(
        verbose_name='CTR. Показатель кликабельности, отношение числа кликов к количеству показов, %',
        blank=True,
        null=True
    )
    cpc = models.FloatField(
        verbose_name='CPC. Средняя стоимость клика, ₽.',
        blank=True,
        null=True
    )
    summ = models.FloatField(
        verbose_name='Затраты, ₽.',
        blank=True,
        null=True
    )
    atbs = models.IntegerField(
        verbose_name='Добавления в корзину',
        blank=True,
        null=True
    )
    orders = models.IntegerField(
        verbose_name='Количество заказов',
        blank=True,
        null=True
    )
    cr = models.IntegerField(
        verbose_name='CR(conversion rate). Отношение количества заказов к общему количеству посещений кампании',
        blank=True,
        null=True
    )
    shks = models.IntegerField(
        verbose_name='Количество заказанных товаров, шт.',
        blank=True,
        null=True
    )
    sum_price = models.FloatField(
        verbose_name='Заказов на сумму, ₽',
        blank=True,
        null=True
    )

    def __str__(self):
        return f'{self.campaign_number} {self.campaign_name}'

    class Meta:
        verbose_name = 'Общее описание рекламной кампании ВБ'
        verbose_name_plural = 'Общее описание рекламной кампании ВБ'
