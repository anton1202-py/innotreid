from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import CharField, ModelForm, PasswordInput, TextInput

from .models import Articles, Sales, ShelvingStocks, Stocks


class ArticlesForm(ModelForm):
    class Meta:
        model = Articles
        fields = ['seller_article', 'title', 'nomenclature', 'article_wb',
                  'article_ozon', 'article_yandex', 'article_sber',
                  'barcode_wb', 'barcode_ozon', 'barcode_yandex',
                  'barcode_sber', 'multiplicity']
        widgets = {
            'seller_article': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Артикул продавца'
            }),
            'title': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Наименование'
            }),
            'nomenclature': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Номенклатура WB'
            }),
            'article_wb': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Артикул WB'
            }),
            'article_ozon': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Артикул OZON'
            }),
            'article_yandex': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Артикул YANDEX'
            }),
            'article_sber': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Артикул SBER'
            }),
            'barcode_wb': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Баркод WB'
            }),
            'barcode_ozon': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Баркод OZON'
            }),
            'barcode_yandex': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Баркод YANDEX'
            }),
            'barcode_sber': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Баркод SBER'
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


class LoginUserForm(AuthenticationForm):
    username = CharField(
        label='Логин',
        widget=TextInput(attrs={'class': 'form-control'})
    )
    password = CharField(
        label='Пароль',
        widget=PasswordInput(attrs={'class': 'form-control'})
    )


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
