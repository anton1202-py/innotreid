from import_export import resources
from .models import Articles, Stocks


class StocksResource(resources.ModelResource):
    class Meta:
        model = Stocks


class ArticlesResource(resources.ModelResource):
    class Meta:
        model = Articles
