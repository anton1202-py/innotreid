from django import forms

from .models import ArticleGroup, Articles, Groups


class XlsxImportForm(forms.Form):
    xlsx_file = forms.FileField()


class FilterChooseGroupForm(forms.Form):
    """Форма отвечает за фильтрацию записей на странице со списком заявок"""
    group_name = forms.ModelChoiceField(
        queryset=Groups.objects.all(),
        required=False,
        empty_label=''
    )
