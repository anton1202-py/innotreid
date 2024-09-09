from create_reklama.models import CreatedCampaign
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
        on_delete=models.SET_NULL,
        verbose_name='Юр. лицо',
        related_name='com_desc_campaign',
        blank=True,
        null=True
    )
    campaign_type = models.SmallIntegerField(
        verbose_name='Тип рекламной кампании',
    )
    campaign_status = models.SmallIntegerField(
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
        CreatedCampaign,
        on_delete=models.SET_NULL,
        verbose_name='Рекламная кампания',
        related_name='main_par_campaign',
        null=True,
        blank=True,
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
        CreatedCampaign,
        on_delete=models.SET_NULL,
        verbose_name='Рекламная кампания',
        related_name='main_clust_campaign',
        blank=True,
        null=True
    )
    cluster = models.ForeignKey(
        'KeywordPhrase',
        on_delete=models.SET_NULL,
        verbose_name='Кластер',
        related_name='main_campaign_cluster',
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
        on_delete=models.SET_NULL,
        verbose_name='Кластер рекламной кампании',
        related_name='main_clust_keyword_campaign',
        blank=True,
        null=True
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
        CreatedCampaign,
        on_delete=models.SET_NULL,
        verbose_name='Рекламная кампания',
        related_name='exclude_main_campaign',
        blank=True,
        null=True
    )
    excluded = models.TextField(
        verbose_name='Минус-фразы для товаров из кампании',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.excluded


class MainArticleCampaignParameters(models.Model):
    """
    Общая статистика артикулов рекламной кампании за все время существования
    Получаем данные из: https://advert-api.wb.ru/adv/v2/fullstats
    https://openapi.wb.ru/promotion/api/ru/#tag/Statistika/paths/~1adv~1v2~1fullstats/post
    """
    campaign = models.ForeignKey(
        CreatedCampaign,
        on_delete=models.SET_NULL,
        verbose_name='Рекламная кампания',
        related_name='main_art_par_campaign',
        blank=True,
        null=True
    )
    article = models.ForeignKey(
        Articles,
        on_delete=models.SET_NULL,
        verbose_name='Артикул',
        related_name='main_art_par_campaign',
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
        CreatedCampaign,
        on_delete=models.SET_NULL,
        verbose_name='Рекламная кампания',
        related_name='daily_params_campaign',
        blank=True,
        null=True
    )
    statistic_date = models.DateField(
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
        CreatedCampaign,
        on_delete=models.SET_NULL,
        verbose_name='Рекламная кампания',
        related_name='daily_article_par_campaign',
        blank=True,
        null=True
    )
    article = models.ForeignKey(
        Articles,
        on_delete=models.SET_NULL,
        verbose_name='Артикул',
        related_name='daily_art_par_campaign',
        blank=True,
        null=True
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
        on_delete=models.SET_NULL,
        verbose_name='Артикул',
        related_name='key_cluster_article',
        blank=True,
        null=True
    )
    cluster = models.ForeignKey(
        'KeywordPhrase',
        on_delete=models.SET_NULL,
        verbose_name='Кластер',
        related_name='main_article_kw',
        blank=True,
        null=True
    )
    views = models.IntegerField(
        verbose_name='Показы',
        blank=True,
        null=True
    )
    source = models.CharField(
        verbose_name='Источник статистики',
        max_length=300,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Статистика запросов из Рекламы ВБ'
        verbose_name_plural = 'Статистика запросов из Рекламы ВБ'


class JamMainArticleKeyWords(models.Model):
    """
    Статистика ключевых кластеров из Джема
    Получаем через загрузку Excel файлов на еженедельной основе.
    """
    article = models.ForeignKey(
        Articles,
        on_delete=models.SET_NULL,
        verbose_name='Артикул',
        related_name='jam_key_cluster_article',
        blank=True,
        null=True
    )
    cluster = models.ForeignKey(
        'KeywordPhrase',
        on_delete=models.SET_NULL,
        verbose_name='Кластер',
        related_name='jam_main_article_cluster',
        blank=True,
        null=True
    )
    date_start = models.DateField(
        verbose_name='Дата начала статистики',
        blank=True,
        null=True
    )
    date_finish = models.DateField(
        verbose_name='Дата конца статистики',
        blank=True,
        null=True
    )
    frequency = models.IntegerField(
        verbose_name='Частота',
        blank=True,
        null=True
    )
    visibility = models.IntegerField(
        verbose_name='Видимость',
        blank=True,
        null=True
    )
    views = models.IntegerField(
        verbose_name='Показы',
        blank=True,
        null=True
    )
    average_position = models.IntegerField(
        verbose_name='Средняя позиция',
        blank=True,
        null=True
    )
    median_position = models.IntegerField(
        verbose_name='Медианная позиция',
        blank=True,
        null=True
    )
    go_to_card = models.IntegerField(
        verbose_name='Переходы в карточку',
        blank=True,
        null=True
    )
    added_to_cart = models.IntegerField(
        verbose_name='Положили в корзину',
        blank=True,
        null=True
    )
    conversion_to_cart = models.FloatField(
        verbose_name='Конверсия в корзину',
        blank=True,
        null=True
    )
    ordered = models.IntegerField(
        verbose_name='Заказали',
        blank=True,
        null=True
    )
    conversion_to_order = models.FloatField(
        verbose_name='Конверсия в заказ',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Статистика запросов из Джема'
        verbose_name_plural = 'Статистика запросов из Джема'


class MainArticleExcluded(models.Model):
    """
    Минус-фразы для артикула
    Если в рекламной кампании один артикул, тогда соотносим 
    все минус слова с этим артикулом.
    """
    article = models.ForeignKey(
        Articles,
        on_delete=models.SET_NULL,
        verbose_name='Артикул',
        related_name='excluded_for_article',
        blank=True,
        null=True
    )
    excluded = models.CharField(
        verbose_name='Минус слово артикула',
        max_length=300
    )

    class Meta:
        verbose_name = 'Минус слово артикула'
        verbose_name_plural = 'Минус слово артикула'


class KeywordPhrase(models.Model):
    """
    Таблица с ключевыми фразами
    """
    phrase = models.CharField(
        verbose_name='Ключевая фраза',
        max_length=300
    )
    campaigns_amount = models.IntegerField(
        verbose_name='Количество кампаний, рекламируемых по фразе',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.phrase

    class Meta:
        verbose_name = 'Ключевые фразы'
        verbose_name_plural = 'Ключевые фразы'


class StatisticCampaignKeywordPhrase(models.Model):
    """
    Статистика ключевых фраз кампании.
    """
    keyword = models.ForeignKey(
        KeywordPhrase,
        on_delete=models.SET_NULL,
        verbose_name='Ключевая фраза',
        related_name='statistic_keyphrase',
        blank=True,
        null=True
    )
    campaign = models.ForeignKey(
        CreatedCampaign,
        on_delete=models.SET_NULL,
        verbose_name='Рекламная кампания',
        related_name='statistic_campaign',
        blank=True,
        null=True
    )
    statistic_date = models.DateTimeField(
        verbose_name='Дата',
        blank=True,
        null=True
    )
    views = models.IntegerField(
        verbose_name='Количество просмотров',
        blank=True,
        null=True
    )

    clicks = models.IntegerField(
        verbose_name='Количество кликов',
        blank=True,
        null=True
    )

    ctr = models.FloatField(
        verbose_name='Click-Through Rate, отношение количества кликов к количеству показов, %',
        blank=True,
        null=True
    )
    summ = models.FloatField(
        verbose_name='Затраты',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Статистика ключевых фраз РК'
        verbose_name_plural = 'Статистика ключевых фраз РК'


class ArticleCampaignWhiteList(models.Model):
    """
    Белый лист фраз артикулов и кампаний, в которых эти артикулы есть
    """
    article = models.ForeignKey(
        Articles,
        on_delete=models.SET_NULL,
        verbose_name='Артикул',
        related_name='white_list_article',
        blank=True,
        null=True
    )
    campaign = models.ForeignKey(
        CreatedCampaign,
        on_delete=models.SET_NULL,
        verbose_name='Рекламная кампания',
        related_name='white_list_campaign',
        blank=True,
        null=True
    )
    keyword = models.ForeignKey(
        KeywordPhrase,
        on_delete=models.SET_NULL,
        verbose_name='Ключевая фраза',
        related_name='white_list_keyphrase',
        blank=True,
        null=True
    )
    phrase_list = models.TextField(
        verbose_name='Список слов артикула в кампании',
        max_length=300
    )

    def __str__(self):
        return self.phrase_list

    class Meta:
        verbose_name = 'Белый лист фраз артикулов и кампаний'
        verbose_name_plural = 'Белый лист фраз артикулов и кампаний'
