from database.models import CodingMarketplaces
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import (CheckboxInput, ChoiceField, FileInput, ModelForm,
                          TextInput)

from .models import TaskCreator


class TaskCreatorForm(ModelForm):
    class Meta:
        model = TaskCreator
        fields = ['task_name', 'market_name',  'remainder',
                  'stickers', 'printing', 'printed', 'shipment_status']
        market_name = forms.ChoiceField(choices=CodingMarketplaces.objects.all())
    
        printing = forms.BooleanField()
        printed = forms.BooleanField()
        shipment_status = forms.BooleanField()
        widgets = {            
            'task_name': TextInput(attrs={
                'class': 'form-control',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(TaskCreatorForm, self).__init__(*args, **kwargs)
        self.fields['market_name'].empty_label = 'Выбрать'