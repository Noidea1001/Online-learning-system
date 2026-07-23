# students/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction  
from .models import Student

User = get_user_model()

class StudentForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={'placeholder': 'Enter username', 'class': 'form-control rounded-3'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'name@example.com', 'class': 'form-control rounded-3'})
    )
    first_name = forms.CharField(
        max_length=150, 
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'First name', 'class': 'form-control rounded-3'})
    )
    last_name = forms.CharField(
        max_length=150, 
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Last name', 'class': 'form-control rounded-3'})
    )
    password = forms.CharField(
        required=False, 
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control rounded-3'}), 
        help_text="Password must be at least 8 characters long"
    )

    class Meta:
        model = Student
        fields = ['date_of_birth', 'gender', 'phone_number', 'profile_picture', 'bio']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-3'}),
            'gender': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Phone number', 'class': 'form-control rounded-3'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control rounded-3'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Short biology or study goals...', 'class': 'form-control rounded-3'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            existing_classes = field.widget.attrs.get('class', '')
            if field_name == 'gender':
                field.widget.attrs['class'] = 'form-select rounded-3'
            else:
                if 'form-control' not in existing_classes:
                    field.widget.attrs['class'] = f"{existing_classes} form-control rounded-3".strip()
        
        if self.instance and self.instance.pk:
            self.fields['password'].required = False
            if getattr(self.instance, 'user', None):
                user = self.instance.user
                self.fields['username'].initial = user.username
                self.fields['email'].initial = user.email
                self.fields['first_name'].initial = user.first_name
                self.fields['last_name'].initial = user.last_name
        else:
            self.fields['password'].required = True

    def clean_username(self):
        username = self.cleaned_data.get('username')
        user_qs = User.objects.filter(username=username)
        if self.instance and self.instance.pk and getattr(self.instance, 'user', None):
            user_qs = user_qs.exclude(pk=self.instance.user.pk)
        if user_qs.exists():
            raise forms.ValidationError("Username already exists in the system.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            user_qs = User.objects.filter(email=email)
            if self.instance and self.instance.pk and getattr(self.instance, 'user', None):
                user_qs = user_qs.exclude(pk=self.instance.user.pk)
            if user_qs.exists():
                raise forms.ValidationError("A user with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')

        if username:
            try:
                existing_user = User.objects.get(username=username)
                if not self.instance.pk and Student.objects.filter(user=existing_user).exists():
                    self.add_error('username', "This user account is already linked to another student profile.")
                elif self.instance.pk and Student.objects.filter(user=existing_user).exclude(pk=self.instance.pk).exists():
                    self.add_error('username', "This user account is already assigned to a different student.")
            except User.DoesNotExist:
                pass
        return cleaned_data

    def save(self, commit=True):
        student = super().save(commit=False)

        try:
            existing_user = student.user
        except Exception:
            existing_user = None

        with transaction.atomic():
            if self.instance and self.instance.pk and existing_user:
                user = existing_user
                user.username = self.cleaned_data.get('username', user.username)
                user.email = self.cleaned_data.get('email', user.email)
                user.first_name = self.cleaned_data.get('first_name', '')
                user.last_name = self.cleaned_data.get('last_name', '')

                if self.cleaned_data.get('password'):
                    user.set_password(self.cleaned_data['password'])

                if commit:
                    user.save()
                    student.save()
            else:
                # ── CREATE MODE ─────────────────────────────────────────────────
                user = User(
                    username=self.cleaned_data.get('username'),
                    email=self.cleaned_data.get('email'),
                    first_name=self.cleaned_data.get('first_name', ''),
                    last_name=self.cleaned_data.get('last_name', ''),
                    role='STUDENT',
                )
                user.set_password(self.cleaned_data.get('password'))

                if commit:
                    user.save()
                    student, _ = Student.objects.get_or_create(user=user)

                    for field in ['gender', 'phone_number', 'bio', 'date_of_birth']:
                        value = self.cleaned_data.get(field)
                        if value is not None:
                            setattr(student, field, value)
                    if self.cleaned_data.get('profile_picture'):
                        student.profile_picture = self.cleaned_data['profile_picture']
                    student.save()

        return student
