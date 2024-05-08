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


class DesinerArticleForm(forms.ModelForm):
    class Meta:
        model = Articles
        fields = ['designer_article']
        widgets = {
            'designer_article': forms.CheckboxInput(),
        }


class UploadFileForm(forms.Form):
    file = forms.FileField()
