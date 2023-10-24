from django.contrib import admin
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget

from .models import TaskCreator

admin.site.register(TaskCreator)


