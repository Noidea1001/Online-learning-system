# instructors/forms.py
from django import forms
from django.contrib.auth import get_user_model
from .models import Instructor

User = get_user_model()

class InstructorUserForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=User.Role.choices if hasattr(User, 'Role') else [('INSTRUCTOR', 'Instructor'), ('EMPLOYEE', 'Employee')],
        widget=forms.Select(attrs={'class': 'form-control form-select rounded-3'}),
        initial='INSTRUCTOR',
        label="User Account Role",
        required=False 
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter secure password', 'class': 'form-control rounded-3'}),
        required=False, 
        help_text="Password parameters require an alphanumeric combination."
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control rounded-3'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email address', 'class': 'form-control rounded-3'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First name', 'class': 'form-control rounded-3'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last name', 'class': 'form-control rounded-3'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.instance or not self.instance.pk:
            self.fields['password'].required = True
            
        for field_name, field in self.fields.items():
            existing_classes = field.widget.attrs.get('class', '')
            if field_name == 'role':
                field.widget.attrs['class'] = 'form-control form-select rounded-3'
            else:
                if 'form-control' not in existing_classes:
                    field.widget.attrs['class'] = f"{existing_classes} form-control rounded-3".strip()

    def clean_username(self):
        username = self.cleaned_data.get('username')
        qs = User.objects.filter(username=username)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A user with this username already exists in the system.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = User.objects.filter(email=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("An account with this email address already exists in the system.")
        return email


class InstructorForm(forms.ModelForm):
    class Meta:
        model = Instructor
        fields = ['specialty', 'experience_years', 'bio'] 
        widgets = {
            'specialty': forms.TextInput(attrs={'placeholder': 'e.g., Senior Web Developer, Data Scientist', 'class': 'form-control rounded-3'}),
            'experience_years': forms.NumberInput(attrs={'min': 0, 'placeholder': 'Years of experience', 'class': 'form-control rounded-3'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Brief description of your professional background and academic records...', 'class': 'form-control rounded-3'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing_classes = field.widget.attrs.get('class', '')
            if 'form-control' not in existing_classes:
                field.widget.attrs['class'] = f"{existing_classes} form-control rounded-3".strip()
