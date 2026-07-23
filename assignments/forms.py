# assignments/forms.py
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Assignment
from lessons.models import Lesson
from courses.models import Course

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['course', 'lesson', 'title', 'description', 'due_date', 'max_score', 'assignment_file']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the requirements or conditions of the assignment...'}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'assignment_file': forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        instructor = kwargs.pop('instructor', None)
        is_lms_admin = kwargs.pop('is_lms_admin', False)
        initial_lesson_id = kwargs.pop('initial_lesson_id', None)
        
        super().__init__(*args, **kwargs)
        
        self.fields['lesson'].required = False
        self.fields['lesson'].empty_label = "Course-Wide Task"
        self.fields['course'].empty_label = "Select Course"

        for field_name, field in self.fields.items():
            existing_classes = field.widget.attrs.get('class', '')
            if field_name not in ['assignment_file']:
                field.widget.attrs['class'] = f"{existing_classes} form-control rounded-3".strip()

        if instructor:
            if is_lms_admin:
                self.fields['course'].queryset = Course.objects.all()
            else:
                self.fields['course'].queryset = Course.objects.filter(instructor__user=instructor)

        if initial_lesson_id:
            try:
                target_lesson = Lesson.objects.get(id=initial_lesson_id)
                self.initial['lesson'] = target_lesson
                self.initial['course'] = target_lesson.course
                
                self.fields['lesson'].queryset = Lesson.objects.filter(course=target_lesson.course)
                
            except Lesson.DoesNotExist:
                pass
        elif 'course' in self.data:
            try:
                course_id = int(self.data.get('course'))
                self.fields['lesson'].queryset = Lesson.objects.filter(course_id=course_id)
            except (ValueError, TypeError):
                self.fields['lesson'].queryset = Lesson.objects.none()
        elif self.instance.pk and self.instance.course:
            self.fields['lesson'].queryset = Lesson.objects.filter(course=self.instance.course)
        else:
            if instructor and not is_lms_admin:
                my_courses = Course.objects.filter(instructor__user=instructor)
                self.fields['lesson'].queryset = Lesson.objects.filter(course__in=my_courses)
            else:
                self.fields['lesson'].queryset = Lesson.objects.all()
