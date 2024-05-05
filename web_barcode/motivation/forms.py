from django import forms
from price_system.models import Articles, DesignUser
from users.models import InnotreidUser


class DesignerChooseForm(forms.Form):
    """Форма отвечает за фильтрацию записей на странице со списком заявок"""
    designer_name = forms.ModelChoiceField(
        queryset=InnotreidUser.objects.all(),
        required=False,
        empty_label=' '
    )
