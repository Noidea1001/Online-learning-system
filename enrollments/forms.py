# enrollments/forms.py
from django import forms
from .models import Enrollment
from students.models import Student
from courses.models import Course

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['student', 'course', 'is_paid']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'course': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.fields['student'].empty_label = "Select Active Student"
        self.fields['course'].empty_label = "Select Target Course"
        if user:
            if user.is_superuser or getattr(user, 'role', None) == 'EMPLOYEE':
                self.fields['student'].queryset = Student.objects.all().select_related('user')
                self.fields['course'].queryset = Course.objects.all()
            
            elif getattr(user, 'role', None) == 'INSTRUCTOR':
                self.fields['course'].queryset = Course.objects.filter(instructor__user=user)
                self.fields['student'].queryset = Student.objects.all().select_related('user')
                self.fields['is_paid'].widget.attrs['disabled'] = 'disabled'
            
            else:
                if hasattr(user, 'student_profile'):
                    self.fields['student'].queryset = Student.objects.filter(id=user.student_profile.id)
                    self.initial['student'] = user.student_profile
                    self.fields['student'].widget.attrs['style'] = 'pointer-events: none; background-color: #e9ecef;'
                    self.fields['is_paid'].widget.attrs['disabled'] = 'disabled'

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.pk:
            if 'is_paid' in self.fields and self.fields['is_paid'].widget.attrs.get('disabled'):
                cleaned_data['is_paid'] = self.instance.is_paid
        return cleaned_data
