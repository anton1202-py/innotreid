from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Groups


class GroupsAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'wb_price', 'wb_discount',
                    'ozon_price', 'yandex_price', 'min_price', 'old_price')


admin.site.register(Groups, GroupsAdmin)
