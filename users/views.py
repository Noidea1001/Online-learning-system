# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import SignUpForm, UserProfileForm
from courses.models import Course
from students.models import Student
from instructors.models import Instructor
from employees.models import Employee


@login_required
def profile_edit(request):
    """View to edit account profile details and avatar picture."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save()

            # Also sync profile_picture to student_profile or employee_profile if present
            if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                student = user.student_profile
                if user.profile_picture:
                    student.profile_picture = user.profile_picture
                student.save()
            elif user.role == 'EMPLOYEE' and hasattr(user, 'employee_profile'):
                employee = user.employee_profile
                if user.profile_picture:
                    employee.image = user.profile_picture
                employee.save()

            messages.success(request, "Your profile photo and details have been updated successfully!")
            return redirect('profile_edit')
        else:
            messages.error(request, "Failed to update profile. Please check the form errors below.")
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'users/profile_edit.html', {'form': form})


def homepage(request):
    """Public Homepage - Fully dynamic from database"""
    User = get_user_model()
    
    context = {
        'featured_courses': Course.objects.filter(is_published=True)[:6],
        
        # Dynamic statistics
        'total_courses_count': Course.objects.filter(is_published=True).count(),
        'total_instructors_count': Instructor.objects.count(),
        'total_students_count': User.objects.filter(role='STUDENT').count(),
    }
    return render(request, 'homepage.html', context)


@login_required
def dashboard_redirect(request):

    return redirect('dashboard_home')


def register(request):
    """User Registration - Safe & Clean Architecture"""
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            
            messages.success(request, 'Registration successful. Please log in to your dashboard.')
            return redirect('login')
        else:
            messages.error(request, 'Registration failed. Please correct the validation errors below.')
    else:
        form = SignUpForm()

    return render(request, 'registration/register.html', {'form': form})
