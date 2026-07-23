# submissions/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Submission

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['submitted_file', 'text_content']
        widgets = {
            'submitted_file': forms.FileInput(attrs={'class': 'form-control rounded-3'}),
            'text_content': forms.Textarea(attrs={
                'class': 'form-control rounded-3', 
                'rows': 4, 
                'placeholder': 'Type your answer, description, or paste your project URLs here...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing_classes = field.widget.attrs.get('class', '')
            if 'form-control' not in existing_classes:
                field.widget.attrs['class'] = f"{existing_classes} form-control rounded-3".strip()

    def clean_submitted_file(self):
        file = self.cleaned_data.get('submitted_file')
        if file:
            max_size = 25 * 1024 * 1024  # 25MB
            if file.size > max_size:
                raise ValidationError("File exceeds the maximum size limit of 25MB.")
        return file

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('submitted_file')
        text = cleaned_data.get('text_content')

        if not file and not text:
            raise ValidationError("You must either upload a file or provide text content to submit this assignment.")
        return cleaned_data


class GradeForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['score', 'feedback']
        widgets = {
            'score': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'step': '0.1', 'min': '0', 'placeholder': '0.0'}),
            'feedback': forms.Textarea(attrs={
                'class': 'form-control rounded-3', 
                'rows': 3,
                'placeholder': 'Provide constructive feedback, notes, or improvement remarks for the student...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing_classes = field.widget.attrs.get('class', '')
            if 'form-control' not in existing_classes:
                field.widget.attrs['class'] = f"{existing_classes} form-control rounded-3".strip()

    def clean_score(self):
        score = self.cleaned_data.get('score')
        
        if score is not None and self.instance and hasattr(self.instance, 'assignment'):
            max_score = self.instance.assignment.max_score
            if score > max_score:
                raise ValidationError(f"The score cannot exceed the assignment's maximum score of {max_score}.")
        return score
