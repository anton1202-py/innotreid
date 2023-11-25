from django.contrib import admin
from ozon_system.models import (AdvGroup, GroupActions, GroupCeleryAction,
                                GroupCompaign)

# Register your models here.


admin.site.register(AdvGroup)
admin.site.register(GroupCompaign)
admin.site.register(GroupActions)
admin.site.register(GroupCeleryAction)
