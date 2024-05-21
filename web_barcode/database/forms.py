from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import CharField, ModelForm, PasswordInput, TextInput

from .models import Articles, Sales, ShelvingStocks, Stocks


class ArticlesForm(ModelForm):
    class Meta:
        model = Articles
        fields = ['common_article', 'title', 'article_seller_wb', 'article_wb_nomenclature',
                  'barcode_wb', 'article_seller_ozon', 'ozon_product_id', 'fbo_ozon_sku_id',
                  'fbs_ozon_sku_id', 'barcode_ozon', 'article_seller_yandex', 'barcode_yandex',
                  'sku_yandex', 'multiplicity']
        widgets = {
            'common_article': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Общий артикул',
            }),
            'title': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Наименование'
            }),
            'article_seller_wb': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Артикул постащика на WB'
            }),
            'article_wb_nomenclature': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Номенклатура WB'
            }),
            'barcode_wb': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Баркод WB'
            }),
            'article_seller_ozon': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Артикул поставщика на OZON'
            }),
            'ozon_product_id': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'OZON Product ID'
            }),
            'fbo_ozon_sku_id': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'FBO OZON SKU ID'
            }),
            'fbs_ozon_sku_id': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'FBS OZON SKU ID'
            }),
            'barcode_ozon': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Баркод OZON'
            }),
            'article_seller_yandex': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Артикул поставщика на YANDEX'
            }),
            'barcode_yandex': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Баркод YANDEX'
            }),
            'sku_yandex': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SKU YANDEX'
            }),
            'multiplicity': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Кратность'
            })
        }


class StocksForm(ModelForm):
    class Meta:
        model = Stocks
        fields = ['seller_article', 'article_marketplace',
                  'code_marketplace', 'amount']
        widgets = {
            'seller_article': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Артикул продавца'
            }),
            'article_marketplace': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Артикул маркетплейса'
            }),
            'code_marketplace': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Код маркетплейса'
            }),
            'amount': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Количество'
            })
        }


class ShelvingForm(ModelForm):
    class Meta:
        model = ShelvingStocks
        fields = ['seller_article_wb', 'seller_article',
                  'shelf_number', 'amount']
        widgets = {
            'seller_article_wb': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Артикул продавца на Wildberries'
            }),
            'seller_article': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Артикул продавца'
            }),
            'shelf_number': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Номер ячейки'
            }),
            'amount': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Остаток в ячейке'
            })
        }


class LoginUserForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class SalesForm(ModelForm):
    class Meta:
        model = Sales
        fields = ['article_marketplace', 'amount', 'avg_price_sale',
                  'sum_sale', 'sum_pay', 'code_marketplace']
        widgets = {
            'article_marketplace': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Артикул маркетплейса'
            }),
            'amount': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Количество'
            }),
            'avg_price_sale': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Средняя цена'
            }),
            'sum_sale': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Сумма продажи'
            }),
            'sum_pay': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Сумма выплат'
            }),
            'code_marketplace': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Код маркетплейса'
            })
        }


class SelectDateForm(forms.Form):
    datestart = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'class': 'choose-date',
        }))
    datefinish = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'class': 'choose-date',
        }))
    article_filter = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }))


class SelectDateStocksForm(forms.Form):
    datestart = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'class': 'choose-date',
        }))
    datefinish = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'class': 'choose-date',
        }))
    article_filter = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }))
    stock_filter = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }))


class SelectArticlesForm(forms.Form):
    article_filter = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        }))
