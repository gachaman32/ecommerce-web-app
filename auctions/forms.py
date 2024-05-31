from django.forms import ModelForm
from django import forms

from .models import *

class whenCreatingListingForms(forms.Form):
    title = forms.CharField(label="Title")
    desc = forms.CharField(widget=forms.Textarea)
    bid = forms.CharField(widget=forms.NumberInput)
    imgLink = forms.CharField(required=False, widget=forms.URLInput())