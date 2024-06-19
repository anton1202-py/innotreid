from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from price_system.models import Articles
from reklama.models import UrLico
from users.models import InnotreidUser


class FeedbacksWildberries(models.Model):
    """Отзывы с Wildberries на все товары из таблицы Articles"""
    common_article = models.ForeignKey(
        Articles,
        verbose_name='Общий артикул',
        on_delete=models.SET_NULL,
        null=True,
    )
    ur_lico = models.ForeignKey(
        UrLico,
        verbose_name='Общий артикул',
        on_delete=models.SET_NULL,
        null=True,
    )
    feedbackid = models.CharField(
        verbose_name='ID отзыва',
        max_length=100,
    )

    user_name = models.CharField(
        verbose_name='Имя автора отзыва',
        max_length=300,
        blank=True,
        null=True
    )
    text = models.TextField(
        verbose_name='Текст отзыва',
        blank=True,
        null=True,
    )
    product_valuation = models.IntegerField(
        verbose_name='Оценка товара от покупателя',
        blank=True,
        null=True,
    )
    created_date = models.DateTimeField(
        verbose_name='Дата и время создания отзыва',
        blank=True,
        null=True
    )
    state = models.CharField(
        # none - не обработан (новый)
        # wbRu - обработан
        verbose_name='Статус отзыва',
        max_length=50,
        blank=True,
        null=True,
    )
    was_viewed = models.BooleanField(
        verbose_name='Просмотрен ли отзыв',
        blank=True,
        null=True,
    )
    is_able_supplier_feedback_valuation = models.BooleanField(
        verbose_name='Доступна ли продавцу оценка отзыва',
        blank=True,
        null=True,
    )
    supplier_feedback_valuation = models.IntegerField(
        verbose_name='Оценка отзыва, оставленная продавцом',
        blank=True,
        null=True,
    )
    is_able_supplier_product_valuation = models.BooleanField(
        verbose_name='Доступна ли продавцу оценка товара',
        blank=True,
        null=True,
    )
    supplier_product_valuation = models.IntegerField(
        verbose_name='Оценка товара, оставленная продавцом',
        blank=True,
        null=True,
    )
    is_able_return_product_orders = models.BooleanField(
        verbose_name='Доступна ли товару опция возврата',
        blank=True,
        null=True,
    )
    return_product_orders_date = models.DateTimeField(
        verbose_name='Дата и время, когда на запрос возврата был получен ответ со статус-кодом 200.',
        blank=True,
        null=True
    )
    bables = models.TextField(
        verbose_name='Список тегов покупателя',
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.common_article.common_article

    class Meta:
        verbose_name = 'Отзывы на товары с Wildberries'
        verbose_name_plural = 'Отзывы на товары с Wildberries'


class WildberriesAnswerFeedback(models.Model):
    """
    Ответ на отзыв Wildberries

    Статусы ответа:
    none - новый
    wbRu - отображается на сайте
    reviewRequired - ответ проходит проверку
    rejected - ответ отклонён

    """
    feedback = models.OneToOneField(
        FeedbacksWildberries,
        on_delete=models.SET_NULL,
        null=True,)
    text = models.TextField(
        verbose_name='Текст ответа',
        blank=True,
        null=True,
    )
    answer_state = models.TextField(
        verbose_name='Статус ответа',
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.feedback

    class Meta:
        verbose_name = 'Ответ на отзыв'
        verbose_name_plural = 'Ответ на отзыв'


class ProductDetails(models.Model):
    """Структура товара, на который написан отзыв"""
    feedback = models.OneToOneField(
        FeedbacksWildberries,
        verbose_name='Отзыв',
        on_delete=models.SET_NULL,
        null=True,)
    nmid = models.IntegerField(
        verbose_name='Артикул WB',
        blank=True,
        null=True,
    )
    imtid = models.IntegerField(
        verbose_name='Идентификатор карточки товара',
        blank=True,
        null=True,
    )
    product_name = models.CharField(
        max_length=255,
        verbose_name='Название товара',
        blank=True,
        null=True,)
    supplier_article = models.CharField(
        max_length=100,
        verbose_name='Артикул продавца',
        blank=True,
        null=True,)
    supplier_name = models.CharField(
        max_length=100,
        verbose_name='Имя продавца',
        blank=True,
        null=True,)
    brand_name = models.CharField(
        max_length=50,
        verbose_name='Бренд товара',
        blank=True,
        null=True,)
    size = models.CharField(
        max_length=20,
        verbose_name='Размер товара',
        blank=True,
        null=True,)

    def __str__(self):
        return self.feedback

    class Meta:
        verbose_name = 'Товар отзыва'
        verbose_name_plural = 'Товар отзыва'


class PhotoLinks(models.Model):
    feedback = models.OneToOneField(
        FeedbacksWildberries,
        verbose_name='Отзыв',
        on_delete=models.SET_NULL,
        null=True,)
    full_size = models.URLField(
        verbose_name='Адрес фотографии полного размера',
        blank=True,
        null=True,
    )
    mini_size = models.URLField(
        verbose_name='Адрес фотографии маленького размера',
        blank=True,
        null=True,
    )
    full_size_photo = models.ImageField(
        verbose_name='Фото из отзыва',
        upload_to="feedback_images/",
        blank=True,
        null=True,)

    def __str__(self):
        return self.feedback

    class Meta:
        verbose_name = 'Фото товара из отзыва'
        verbose_name_plural = 'Фото товара из отзыва'
