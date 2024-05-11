from django.contrib.auth.models import Group, User
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from price_system.models import DesignUser

from .models import InnotreidUser


@receiver(m2m_changed, sender=Group.user_set.through)
def add_user_to_another_table(sender, instance, action, reverse, model, pk_set, **kwargs):
    """Если Пользователю присваивается группа Дизайнеры, то он добавляется в таблицу DesignUser"""
    if instance.groups.filter(name='Дизайнеры').exists():
        if not DesignUser.objects.filter(designer=instance).exists():
            DesignUser(designer=instance).save()
