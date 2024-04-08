from django.core.signals import request_finished
from django.db.models.signals import post_save
from django.dispatch import receiver
from price_system.models import Articles
from reklama.models import DataOooWbArticle, OooWbArticle


@receiver(post_save, sender=Articles)
def create_related_model(sender, instance, created, **kwargs):
    if created:
        DataOooWbArticle.objects.get_or_create(wb_article=instance)
