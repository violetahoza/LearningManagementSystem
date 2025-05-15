from django import forms
from .models import Quiz, Question, Answer
import json

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'total_marks']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'question_type', 'correct_answer', 'options']
        widgets = {
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'question_type': forms.Select(attrs={'class': 'form-control', 'id': 'question-type-select'}),
            'correct_answer': forms.TextInput(attrs={'class': 'form-control'}),
            'options': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'id': 'options-field',
                'placeholder': 'For multiple choice questions, enter each option on a new line'
            }),
        }
    
    def clean_options(self):
        question_type = self.cleaned_data.get('question_type')
        options = self.cleaned_data.get('options')
        
        if question_type == Question.MULTIPLE_CHOICE:
            if not options:
                raise forms.ValidationError("Options are required for multiple choice questions")
            
            # Convert lines to a list and filter empty lines
            option_list = [opt.strip() for opt in options.split('\n') if opt.strip()]
            
            if len(option_list) < 2:
                raise forms.ValidationError("At least two options are required")
            
            # Convert to JSON for storage
            return json.dumps(option_list)
        
        return options
    
    def clean(self):
        cleaned_data = super().clean()
        question_type = cleaned_data.get('question_type')
        correct_answer = cleaned_data.get('correct_answer')
        options = cleaned_data.get('options')
        
        if question_type == Question.MULTIPLE_CHOICE and options:
            # Check if correct answer is in options
            option_list = json.loads(options)
            if correct_answer not in option_list:
                self.add_error('correct_answer', "Correct answer must be one of the options")
        
        if question_type == Question.TRUE_FALSE:
            if correct_answer.lower() not in ['true', 'false']:
                self.add_error('correct_answer', "Correct answer must be 'true' or 'false'")
        
        return cleaned_data

class QuizAttemptForm(forms.Form):
    """A dynamic form for attempting a quiz"""
    def __init__(self, *args, **kwargs):
        # Get questions from kwargs
        questions = kwargs.pop('questions', None)
        super().__init__(*args, **kwargs)
        
        if questions:
            for question in questions:
                field_name = f'question_{question.id}'
                
                if question.question_type == Question.MULTIPLE_CHOICE:
                    # For multiple choice, create a select field
                    choices = [(opt, opt) for opt in json.loads(question.options)]
                    self.fields[field_name] = forms.ChoiceField(
                        label=question.question_text,
                        choices=choices,
                        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
                    )
                elif question.question_type == Question.TRUE_FALSE:
                    # For true/false, create a radio field
                    self.fields[field_name] = forms.ChoiceField(
                        label=question.question_text,
                        choices=[('true', 'True'), ('false', 'False')],
                        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
                    )
                else:
                    # For short answer, create a text field
                    self.fields[field_name] = forms.CharField(
                        label=question.question_text,
                        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
                    )