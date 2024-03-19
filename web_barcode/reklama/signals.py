from django.core.signals import request_finished
from django.db.models.signals import post_save
from django.dispatch import receiver
from reklama.models import DataOooWbArticle, OooWbArticle


@receiver(post_save, sender=OooWbArticle)
def create_related_model(sender, instance, created, **kwargs):
    if created:
        DataOooWbArticle.objects.get_or_create(wb_article=instance)
