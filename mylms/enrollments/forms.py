from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django import forms
from .models import Enrollment

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

class EnrollmentStatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=Enrollment.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    # Add student feedback field for when a student drops a course
    feedback = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Please let us know why you\'re dropping this course (optional)'
        })
    )
    
    # Only show the feedback field when status is 'dropped'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'status' in self.data and self.data['status'] != Enrollment.DROPPED:
            self.fields['feedback'].widget = forms.HiddenInput()