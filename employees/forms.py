# employees/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction  
from .models import Employee

User = get_user_model()

class EmployeeForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={'placeholder': 'Enter username', 'class': 'form-control rounded-3'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Enter email address', 'class': 'form-control rounded-3'})
    )
    password = forms.CharField(
        required=False, 
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter password', 'class': 'form-control rounded-3'}),
        help_text="Password parameters require a strong secure combination."
    )
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'form-control rounded-3'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'form-control rounded-3'}))
    phone_number = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Phone Number', 'class': 'form-control rounded-3'}))

    class Meta:
        model = Employee
        fields = ['job_title', 'department', 'salary', 'hire_date', 'image']
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-3'}),
            'salary': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0.00', 'class': 'form-control rounded-3'}),
            'job_title': forms.TextInput(attrs={'placeholder': 'Job Title', 'class': 'form-control rounded-3'}),
            'department': forms.TextInput(attrs={'placeholder': 'Department', 'class': 'form-control rounded-3'}),
            'image': forms.FileInput(attrs={'class': 'form-control rounded-3'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.instance or not self.instance.pk:
            self.fields['password'].required = True
        
        if self.instance and self.instance.pk and getattr(self.instance, 'user', None):
            user = self.instance.user
            self.fields['username'].initial = user.username
            self.fields['email'].initial = user.email
            self.fields['first_name'].initial = getattr(user, 'first_name', '')
            self.fields['last_name'].initial = getattr(user, 'last_name', '')
            self.fields['phone_number'].initial = getattr(user, 'phone_number', '')

        for field in self.fields.values():
            existing_classes = field.widget.attrs.get('class', '')
            if 'form-control' not in existing_classes:
                field.widget.attrs['class'] = f"{existing_classes} form-control rounded-3".strip()

    def clean_username(self):
        username = self.cleaned_data.get('username')
        user_qs = User.objects.filter(username=username)
        
        if self.instance and self.instance.pk and getattr(self.instance, 'user', None):
            user_qs = user_qs.exclude(id=self.instance.user.id)
            
        if user_qs.exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            user_qs = User.objects.filter(email=email)
            
            if self.instance and self.instance.pk and getattr(self.instance, 'user', None):
                user_qs = user_qs.exclude(id=self.instance.user.id)
                
            if user_qs.exists():
                raise forms.ValidationError("A user with this email address already exists.")
        return email

    def save(self, commit=True):
        employee = super().save(commit=False)

        try:
            existing_user = employee.user
        except Exception:
            existing_user = None

        with transaction.atomic():
            if self.instance and self.instance.pk and existing_user:
                # ── UPDATE MODE ─────────────────────────────────────────────────
                user = existing_user
                user.username = self.cleaned_data.get('username', user.username)
                user.email = self.cleaned_data.get('email', user.email)

                if self.cleaned_data.get('password'):
                    user.set_password(self.cleaned_data['password'])
            else:
                # ── CREATE MODE ─────────────────────────────────────────────────
                user = User(
                    username=self.cleaned_data.get('username'),
                    email=self.cleaned_data.get('email'),
                    role='EMPLOYEE',
                )
                user.set_password(self.cleaned_data.get('password'))

                if commit:
                    user.save()
                    employee, _ = Employee.objects.get_or_create(user=user)

            if hasattr(user, 'first_name'):
                user.first_name = self.cleaned_data.get('first_name', '')
            if hasattr(user, 'last_name'):
                user.last_name = self.cleaned_data.get('last_name', '')
            if hasattr(user, 'phone_number'):
                user.phone_number = self.cleaned_data.get('phone_number', '')

            # Apply Employee-specific fields
            employee.job_title = self.cleaned_data.get('job_title', '')
            employee.department = self.cleaned_data.get('department', '')
            if self.cleaned_data.get('salary') is not None:
                employee.salary = self.cleaned_data.get('salary')
            if self.cleaned_data.get('hire_date'):
                employee.hire_date = self.cleaned_data.get('hire_date')
            if self.cleaned_data.get('image'):
                employee.image = self.cleaned_data.get('image')

            if commit:
                user.save()
                employee.save()

        return employee
