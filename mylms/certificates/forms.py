from django import forms
from django.utils import timezone
from django.core.validators import RegexValidator
from .models import Certificate

class CertificateVerifyForm(forms.Form):
    certificate_code = forms.CharField(
        max_length=50, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter certificate code'
        }),
        validators=[
            RegexValidator(
                regex=r'^[0-9]+-[0-9]+-[A-Z0-9]+$',
                message='Invalid certificate code format. Expected format: USER-COURSE-CODE'
            )
        ]
    )