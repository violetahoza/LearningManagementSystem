from django import forms
from .models import Enrollment

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class EnrollmentStatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=Enrollment.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )