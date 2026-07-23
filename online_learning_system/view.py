# online_learning_system/views.py
from django.shortcuts import render
from courses.models import Course
from students.models import Student
from instructors.models import Instructor

def home(request):
    context = {
        'featured_courses': Course.objects.filter(is_published=True, is_featured=True)[:6],
        'total_students_count': Student.objects.count(),
        'total_courses_count': Course.objects.filter(is_published=True).count(),
        'total_instructors_count': Instructor.objects.count(),
    }
    return render(request, 'homepage.html', context)