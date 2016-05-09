from django import forms
from django.forms.widgets import Input

import re

#For all choices, we want the dropdown value to be what's submitted in the form
#That's why we have duplicate entries

CONFIDENCE_CHOICES = (
     ('CA', 'CA'), ('SA', 'SA'), ('A', 'A'), ('N', 'N'), ('D', 'D'),('SD', 'SD'), ('CD', 'CD'), 
)


class DataEntryForm(forms.Form):    
    csv_file = forms.FileField()


class RaterConfForm(forms.Form):   
    confidence_name = forms.CharField(max_length=50, widget=forms.Select(choices=CONFIDENCE_CHOICES))
    