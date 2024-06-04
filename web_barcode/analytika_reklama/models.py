from django.db import models
from django.urls import reverse
from price_system.models import Articles
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

    Получаем данные из: https://advert-api.wb.ru/adv/v1/promotion/adverts
    https://openapi.wb.ru/promotion/api/ru/#tag/Prodvizhenie/paths/~1adv~1v1~1promotion~1adverts/post
    Допускается 5 запросов в секунду.
    Список ID кампаний. Максимум 50.
    """
    campaign_number = models.CharField(
        verbose_name='ID рекламной кампании ВБ',
        max_length=20
    )

    campaign_name = models.CharField(
        verbose_name='Название рекламной кампании ВБ',
        max_length=300
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
    articles_amount = models.SmallIntegerField(
        verbose_name='Количество артикулов',
        blank=True,
        null=True
    )
    articles_name = models.JSONField(
        verbose_name='Названия артикулов',
        blank=True,
        null=True
    )
    create_date = models.DateTimeField(
        verbose_name='Дата создания',
        blank=True,
        null=True
    )
    change_date = models.DateTimeField(
        verbose_name='Дата изменения',
        blank=True,
        null=True
    )
    start_date = models.DateTimeField(
        verbose_name='Дата последнего запуска',
        blank=True,
        null=True
    )
    finish_date = models.DateTimeField(
        verbose_name='Дата завершения кампании',
        blank=True,
        null=True
    )

    def __str__(self):
        return f'{self.campaign_number} {self.campaign_name}'

    class Meta:
        verbose_name = 'Общее описание рекламной кампании ВБ'
        verbose_name_plural = 'Общее описание рекламной кампании ВБ'


class MainCampaignParameters(models.Model):
    """
    Общая статистика рекламной кампании ВБ за все время существования
    Получаем данные из: https://advert-api.wb.ru/adv/v2/fullstats
    https://openapi.wb.ru/promotion/api/ru/#tag/Statistika/paths/~1adv~1v2~1fullstats/post
    """
    campaign = models.ForeignKey(
        CommonCampaignDescription,
        on_delete=models.CASCADE,
        verbose_name='Рекламная кампания',
        related_name='main_par_campaign'
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
        default=0,
        blank=True
    )

    def __str__(self):
        return f'{self.campaign.campaign_number} {self.campaign.campaign_name}'

    class Meta:
        verbose_name = 'Статистика кампании ВБ'
        verbose_name_plural = 'Статистика кампании ВБ'


class MainCampaignClusters(models.Model):
    """
    Кластеры рекламных кампаний
    Получаем данные из: https://advert-api.wb.ru/adv/v2/auto/stat-words
    https://openapi.wb.ru/promotion/api/ru/#tag/Statistika/paths/~1adv~1v2~1auto~1stat-words/get
    """
    campaign = models.ForeignKey(
        CommonCampaignDescription,
        on_delete=models.CASCADE,
        verbose_name='Рекламная кампания',
        related_name='main_clust_campaign'
    )
    cluster = models.CharField(
        verbose_name='Кластер кампании',
        max_length=300,
        blank=True,
        null=True
    )
    count = models.IntegerField(
        verbose_name='Показы по всем фразам кластера',
        blank=True,
        null=True
    )


class MainCampaignClustersKeywords(models.Model):
    """
    Ключевые слова кластеров рекламных кампаний
    Получаем данные из: https://advert-api.wb.ru/adv/v2/auto/stat-words
    https://openapi.wb.ru/promotion/api/ru/#tag/Statistika/paths/~1adv~1v2~1auto~1stat-words/get
    """
    cluster = models.ForeignKey(
        MainCampaignClusters,
        on_delete=models.CASCADE,
        verbose_name='Кластер рекламной кампании',
        related_name='main_clust_keyword_campaign'
    )
    keywords = models.TextField(
        verbose_name='Ключевые фразы кластера',
        blank=True,
        null=True
    )


class MainCampaignExcluded(models.Model):
    """
    Минус фразы рекламных кампаний
    Получаем данные из: https://advert-api.wb.ru/adv/v2/auto/stat-words
    https://openapi.wb.ru/promotion/api/ru/#tag/Statistika/paths/~1adv~1v2~1auto~1stat-words/get
    """
    campaign = models.ForeignKey(
        CommonCampaignDescription,
        on_delete=models.CASCADE,
        verbose_name='Рекламная кампания',
        related_name='exclude_main_campaign'
    )
    excluded = models.TextField(
        verbose_name='Минус-фразы для товаров из кампании',
        blank=True,
        null=True
    )


class MainArticleCampaignParameters(models.Model):
    """
    Общая статистика артикулов рекламной кампании за все время существования
    Получаем данные из: https://advert-api.wb.ru/adv/v2/fullstats
    https://openapi.wb.ru/promotion/api/ru/#tag/Statistika/paths/~1adv~1v2~1fullstats/post
    """
    campaign = models.ForeignKey(
        CommonCampaignDescription,
        on_delete=models.CASCADE,
        verbose_name='Рекламная кампания',
        related_name='main_art_par_campaign'
    )
    article = models.ForeignKey(
        Articles,
        on_delete=models.CASCADE,
        verbose_name='Артикул',
        related_name='main_art_par_campaign'
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
    name = models.CharField(
        verbose_name='Названия артикула',
        max_length=300,
        blank=True,
        null=True
    )
    nmid = models.CharField(
        verbose_name='Ном. номер артикулв у ВБ',
        max_length=20,
        blank=True,
        null=True
    )

    def __str__(self):
        return f'{self.article.common_article} {self.views}'

    class Meta:
        verbose_name = 'Статистика артикулов кампании ВБ'
        verbose_name_plural = 'Статистика артикулов кампании ВБ'


class DailyCampaignParameters(models.Model):
    """
    Ежедневная статистика рекламной кампании ВБ
    Получаем данные из: https://advert-api.wb.ru/adv/v2/fullstats
    https://openapi.wb.ru/promotion/api/ru/#tag/Statistika/paths/~1adv~1v2~1fullstats/post
    """
    campaign = models.ForeignKey(
        CommonCampaignDescription,
        on_delete=models.CASCADE,
        verbose_name='Рекламная кампания',
        related_name='daily_params_campaign'
    )
    statistic_date = models.DateTimeField(
        verbose_name='Дата',
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
        return f'{self.campaign.campaign_number} {self.campaign.campaign_name}'

    class Meta:
        verbose_name = 'Ежедневная статистика кампании ВБ'
        verbose_name_plural = 'Ежедневная статистика кампании ВБ'


class DailyArticleCampaignParameters(models.Model):
    """
    Ежедневная статистика артикулов рекламной кампании
    Получаем данные из: https://advert-api.wb.ru/adv/v2/fullstats
    https://openapi.wb.ru/promotion/api/ru/#tag/Statistika/paths/~1adv~1v2~1fullstats/post
    """
    campaign = models.ForeignKey(
        CommonCampaignDescription,
        on_delete=models.CASCADE,
        verbose_name='Рекламная кампания',
        related_name='daily_article_par_campaign'
    )
    article = models.ForeignKey(
        Articles,
        on_delete=models.CASCADE,
        verbose_name='Артикул',
        related_name='daily_art_par_campaign'
    )
    statistic_date = models.DateTimeField(
        verbose_name='Дата',
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
    name = models.CharField(
        verbose_name='Названия артикула',
        max_length=300,
        blank=True,
        null=True
    )
    nmid = models.CharField(
        verbose_name='Ном. номер артикулв у ВБ',
        max_length=20,
        blank=True,
        null=True
    )
    avg_position = models.IntegerField(
        verbose_name='Средняя позиция товара на страницах поисковой выдачи и каталога',
        blank=True,
        null=True
    )

    def __str__(self):
        return f'{self.article.common_article} {self.views}'

    class Meta:
        verbose_name = 'Ежедневная статистика артикулов кампании ВБ'
        verbose_name_plural = 'Ежедневная статистика артикулов кампании ВБ'


class MainArticleKeyWords(models.Model):
    """
    Ключевые слова и кластеры артикулов
    Если в рекламной кампании один артикул, тогда соотносим все кластеры
    и минус слова рекламной кампании с этим артикулом.

    Получаем данные о расходах и кликах из: https://advert-api.wb.ru/adv/v2/auto/daily-words
    https://openapi.wb.ru/promotion/api/ru/#tag/Statistika/paths/~1adv~1v2~1auto~1daily-words/get

    Получаем данные об общих показах из: https://advert-api.wb.ru/adv/v2/auto/stat-words
    https://openapi.wb.ru/promotion/api/ru/#tag/Statistika/paths/~1adv~1v2~1auto~1stat-words/get

    Если кампания поисковая, получаем данные из:
    Получаем данные об общих показах из: https://advert-api.wb.ru/adv/v1/stat/words
    https://openapi.wb.ru/promotion/api/ru/#tag/Statistika/paths/~1adv~1v1~1stat~1words/get
    """
    article = models.ForeignKey(
        Articles,
        on_delete=models.CASCADE,
        verbose_name='Артикул',
        related_name='key_cluster_article'
    )
    cluster = models.CharField(
        verbose_name='Название кластера',
        max_length=300
    )
    excluded = models.TextField(
        verbose_name='Минус-фразы для артикула',
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
    summ = models.FloatField(
        verbose_name='Затраты, ₽.',
        blank=True,
        null=True
    )
