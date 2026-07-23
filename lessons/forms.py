# lessons/forms.py
from django import forms
from .models import Lesson
from courses.models import Course

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['course', 'title', 'description', 'order', 'video_url', 'video_file', 'pdf_resource']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter lesson title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter lecture notes...'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com...'}),
            'video_file': forms.FileInput(attrs={'class': 'form-control'}),
            'pdf_resource': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            if user.is_superuser or user.role == 'EMPLOYEE':
                self.fields['course'].queryset = Course.objects.all()
            elif user.role == 'INSTRUCTOR':
                instructor_profile = getattr(user, 'instructor_profile', None)
                self.fields['course'].queryset = Course.objects.filter(instructor=instructor_profile)
