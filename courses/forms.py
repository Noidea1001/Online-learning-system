from django import forms
from .models import Course, Tag

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter tag name'}),
        }


class CourseForm(forms.ModelForm):
    # Override is_free as a styled choice field for better UX
    is_free = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        choices=[
            ('True',  'Free'),
            ('False', 'Paid'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Access Type',
        initial=False,
    )

    class Meta:
        model = Course
        fields = ['title', 'description', 'price', 'is_free', 'category', 'instructor', 'image', 'is_published', 'tags']
        widgets = {
            'title':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter course title'}),
            'description':  forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe what students will learn…'}),
            'price':        forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'image':        forms.FileInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input flex-shrink-0', 'style': 'width: 1.25rem; height: 1.25rem; cursor: pointer;'}),
            'category':     forms.Select(attrs={'class': 'form-select'}),
            'instructor':   forms.Select(attrs={'class': 'form-select'}),
            'tags':         forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        self.user = user
        super().__init__(*args, **kwargs)
        
        if user and (user.is_superuser or getattr(user, 'role', None) == 'EMPLOYEE'):
            from instructors.models import Instructor
            self.fields['instructor'].queryset = Instructor.objects.all()
            self.fields['instructor'].required = True
            self.fields['instructor'].label = 'Course Instructor'
            
            # Reordered fields cleanly: Group core context first, pricing middle, images/publishing tags last
            field_order = ['title', 'description', 'is_free', 'price', 'category', 'instructor', 'tags', 'image', 'is_published']
            self.order_fields(field_order)
        else:
            # Hide / delete instructor field for instructor role
            if 'instructor' in self.fields:
                del self.fields['instructor']
                
            # 🛠️ Sorted field dependencies for standard instructors to prevent rendering exceptions
            field_order = ['title', 'description', 'is_free', 'price', 'category', 'tags', 'image', 'is_published']
            self.order_fields(field_order)

    def clean(self):
        cleaned_data = super().clean()
        
        if not cleaned_data.get('instructor') and hasattr(self, 'user') and getattr(self.user, 'role', None) == 'INSTRUCTOR':
            if hasattr(self.user, 'instructor_profile'):
                cleaned_data['instructor'] = self.user.instructor_profile
                
        is_free = cleaned_data.get('is_free')
        if is_free:
            cleaned_data['price'] = 0.00
            
        return cleaned_data

