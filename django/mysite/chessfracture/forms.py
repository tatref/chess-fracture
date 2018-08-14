from django import forms


class FractureForm(forms.Form):
    url = forms.URLField(label='url', max_length=100)
