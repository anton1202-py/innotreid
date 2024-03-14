from celery import current_app
from django.contrib import admin
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget

from .models import Articles, CodingMarketplaces, Reviews, Stocks


class StocksAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,
            {'fields': ['seller_article', 'article_marketplace', 'amount']}
         ),
        ('Информация о дате',
            {'fields': ['code_marketplace'],
             'classes': ['collapse']}
         ),
    ]


# @admin.register(current_app)
# class CeleryTaskAdmin(admin.ModelAdmin):
#     list_display = ['name', 'run', 'apply_async']


admin.site.register(Articles)
admin.site.register(CodingMarketplaces)
admin.site.register(Reviews)
admin.site.register(Stocks, StocksAdmin)


class StockData(resources.ModelResource):
    pub_date = fields.Field(
        column_name='pub_date',
        attribute='pub_date',
        widget=ForeignKeyWidget(Stocks, 'name')
    )
    article_marketplace = fields.Field(
        column_name='article_marketplace',
        attribute='article_marketplace',
        widget=ForeignKeyWidget(Stocks, 'name')
    )
    code_marketplace = fields.Field(
        column_name='code_marketplace',
        attribute='code_marketplace',
        widget=ForeignKeyWidget(Stocks, 'name')
    )
    amount = fields.Field(
        column_name='amount',
        attribute='amount',
        widget=ForeignKeyWidget(Stocks, 'name')
    )

    class Meta:
        model = Stocks
