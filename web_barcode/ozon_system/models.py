from django.db import models


class ArticleAmountRating(models.Model):
    """Модель, которая хранит данных об артикулах и их группах"""
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


class DateActionInfo(models.Model):
    """Модель, показывает данные о начале запуска действия с группой"""
    company_number = models.CharField(
        verbose_name='ID компании',
        blank=True,
        null=True,
    )
    action_type = models.CharField(
        verbose_name='Действие',
        blank=True,
        null=True,
    )
    start_task_datetime = models.DateTimeField(
        verbose_name='Дата и время постановки задачи',
        auto_now_add=True,
    )
    action_datetime = models.DateTimeField(
        verbose_name='Дата и время действия',
        blank=True,
        null=True,
    )
    celery_task = models.CharField(
        verbose_name='ID задачи celery',
        blank=True,
        null=True,
    )


class AdvGroup(models.Model):
    """Модель отображает в админке количество рекламных групп"""
    group = models.PositiveSmallIntegerField(
        verbose_name='Номер рекламной группы'
    )

    def __str__(self):
        return str(self.group)

    class Meta:
        verbose_name = 'Рекламные группы'
        verbose_name_plural = 'Рекламные группы'


class GroupCompaign(models.Model):
    """
    Модель содержит рекламные компании, которые находятся в группах.
    """
    group = models.ForeignKey(
        AdvGroup,
        verbose_name='Номер рекламной группы',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    compaign = models.CharField(
        verbose_name='ID компании',
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.group

    class Meta:
        verbose_name = 'Рекламные компании в группах'
        verbose_name_plural = 'Рекламные компании в группах'


class GroupActions(models.Model):
    """
    Расписание включения и выключения рекламы в группах.
    """
    group = models.ForeignKey(
        AdvGroup,
        verbose_name='Номер рекламной группы',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    action_type = models.CharField(
        verbose_name='Действие',
        blank=True,
        null=True,
    )
    start_task_datetime = models.DateTimeField(
        verbose_name='Дата и время постановки задачи',
        blank=True,
        null=True,
    )
    action_datetime = models.DateTimeField(
        verbose_name='Дата и время действия',
        blank=True,
        null=True,
    )

    def __str__(self):
        return str(self.group.group)

    class Meta:
        verbose_name = 'Включения и выключения рекламы в группах'
        verbose_name_plural = 'Включения и выключения рекламы в группах'


class GroupCeleryAction(models.Model):
    """
    Расписание включения и выключения celery для групп.
    Не отображается для пользователя. Работает под капотом.
    Нужна для того, чтобы пользователь мог отменять задачи celery.
    """

    group_action = models.ForeignKey(
        GroupActions,
        verbose_name='Номер рекламной группы и действия с ней',
        on_delete=models.CASCADE,
        blank=True,
        null=True,

    )
    celery_task = models.CharField(
        verbose_name='ID задачи celery',
        blank=True,
        null=True,
    )

    def __str__(self):
        return str(self.group_action.group), self.celery_task

    class Meta:
        verbose_name = 'Расписание для Celery'
        verbose_name_plural = 'Расписание для Celery'
