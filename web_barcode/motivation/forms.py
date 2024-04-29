from django import forms
from django.contrib.auth.models import User

from .models import Articles, DesignUser


class DesignerChooseForm(forms.Form):
    """Форма отвечает за фильтрацию записей на странице со списком заявок"""
    designer_name = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        empty_label=' '
    )
