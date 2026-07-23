# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class SignUpForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'Last Name'}),
            'username': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'Email Address'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'Optional'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field in self.fields.values():
            existing_classes = field.widget.attrs.get('class', '')
            if 'form-control' not in existing_classes:
                field.widget.attrs['class'] = f"{existing_classes} form-control rounded-3".strip()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'STUDENT'
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'Email Address'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'Phone Number'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control rounded-3', 'accept': 'image/*'}),
        }
