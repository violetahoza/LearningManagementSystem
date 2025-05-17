from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.core.validators import RegexValidator, EmailValidator
from .models import User

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    password = forms.CharField(
        max_length=128, 
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s]*$',
                message='First name should only contain letters and spaces'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s]*$',
                message='Last name should only contain letters and spaces'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    
    email = forms.EmailField(
        max_length=254, 
        required=True,
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    
    role = forms.ChoiceField(
        choices=[
            (User.STUDENT, 'Student'), 
            (User.TEACHER, 'Teacher')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Username',
            'pattern': '^[a-zA-Z0-9._-]+$',
            'title': 'Username can contain letters, numbers, dots, underscores, and hyphens'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Confirm Password'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s]*$',
                message='First name should only contain letters and spaces'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s]*$',
                message='Last name should only contain letters and spaces'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    
    email = forms.EmailField(
        max_length=254, 
        required=True,
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email exists for another user
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with Bootstrap styling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})