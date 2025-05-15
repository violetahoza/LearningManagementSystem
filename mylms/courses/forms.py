from django import forms
from django.utils import timezone
from .models import Course

class DateInput(forms.DateInput):
    input_type = 'date'

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'start_date', 'end_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'start_date': DateInput(attrs={'class': 'form-control'}),
            'end_date': DateInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Validate date range
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError("End date cannot be before start date")
            
            if start_date < timezone.now().date() and not self.instance.pk:
                raise forms.ValidationError("Start date cannot be in the past for new courses")
        
        return cleaned_data