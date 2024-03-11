from django import forms

from .models import UrLico


class FilterUrLicoForm(forms.Form):
    """Форма отвечает за выбор юр. лица"""
    ur_lico_name = forms.ModelChoiceField(
        queryset=UrLico.objects.all(),
        required=False,
        empty_label=''
    )