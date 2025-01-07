from django import forms
from home.models import Document
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('description', 'document', )





