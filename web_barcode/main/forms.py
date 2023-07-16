from django.forms import ModelForm

from . models import AddPostFile


class AddPostSignal(ModelForm):
    class Meta:
        model = AddPostFile
        fields = '__all__'
