from django import forms


class XlsxImportForm(forms.Form):
    xlsx_file = forms.FileField()
