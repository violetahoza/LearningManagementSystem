from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator, EmailValidator
from accounts.models import User

class UserCreationAdminForm(UserCreationForm):
    """Form for creating users by administrators"""
    
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
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'is_active', 'password1', 'password2')
    
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

class UserEditAdminForm(forms.ModelForm):
    """Form for editing users by administrators"""
    
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
    
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'  # Username cannot be changed once created
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email exists for another user
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

class PasswordResetAdminForm(forms.Form):
    """Form for admins to reset a user's password"""
    
    new_password1 = forms.CharField(
        label="New Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password'
        }),
    )
    
    new_password2 = forms.CharField(
        label="Confirm New Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password'
        }),
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2 and password1 != password2:
            self.add_error('new_password2', "The two password fields didn't match.")
        
        return cleaned_data

class NotificationSendForm(forms.Form):
    """Form for admins to send notifications to users"""
    
    RECIPIENT_CHOICES = [
        ('all', 'All Users'),
        ('students', 'All Students'),
        ('teachers', 'All Teachers'),
        ('course', 'Students in a Specific Course'),
    ]
    
    title = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Notification Title'
        })
    )
    
    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Notification Message'
        })
    )
    
    notification_type = forms.ChoiceField(
        choices=[('', 'Select Type')] + list(User.NOTIFICATION_TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    recipient_type = forms.ChoiceField(
        choices=RECIPIENT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'recipient-type-select'
        })
    )
    
    course_id = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'course-select'
        })
    )
    
    def __init__(self, *args, **kwargs):
        courses = kwargs.pop('courses', [])
        super().__init__(*args, **kwargs)
        
        # Populate course choices
        course_choices = [(course.id, course.title) for course in courses]
        self.fields['course_id'].widget.choices = [(0, 'Select Course')] + course_choices
    
    def clean(self):
        cleaned_data = super().clean()
        recipient_type = cleaned_data.get('recipient_type')
        course_id = cleaned_data.get('course_id')
        
        if recipient_type == 'course' and not course_id:
            self.add_error('course_id', "Please select a course.")
        
        return cleaned_data