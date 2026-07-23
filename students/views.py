# students/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.db import transaction
from .models import Student
from .forms import StudentForm  
from enrollments.models import Enrollment  
from submissions.models import Submission 

@login_required
def student_list(request):
    user = request.user
    user_role = str(getattr(user, 'role', '')).strip()
    
    if not user.is_superuser and user_role not in ['EMPLOYEE', 'INSTRUCTOR']:
        raise PermissionDenied
        
    if user.is_superuser or user_role == 'EMPLOYEE':
        students = Student.objects.all().select_related('user').order_by('-id')
    elif user_role == 'INSTRUCTOR':
        instructor_profile = getattr(user, 'instructor_profile', None)
        students = Student.objects.filter(
            enrollments__course__instructor=instructor_profile
        ).select_related('user').distinct().order_by('-id')
    else:
        students = Student.objects.none() 
        
    return render(request, 'students/student_list.html', {'students': students})


@login_required
def student_create(request):
    user_role = str(getattr(request.user, 'role', '')).strip()
    
    # admin and eployee can create
    if request.user.is_superuser or user_role == 'EMPLOYEE':
        pass
    else:
        raise PermissionDenied
        
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                messages.success(request, "Created student profile successfully.")
                return redirect('student_list')
            except Exception as e:
                messages.error(request, "An unexpected database error occurred. Please try again.")
        else:
            messages.error(request, "Failed to create profile. Please check the errors below.")
    else:
        form = StudentForm(user=request.user)
        
    return render(request, 'students/student_form.html', {'form': form})


@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student.objects.select_related('user'), pk=pk)
    user = request.user
    user_role = str(getattr(user, 'role', '')).strip()
    
    is_authorized = user.is_superuser or user_role == 'EMPLOYEE' or student.user == user
    
    if not is_authorized and user_role == 'INSTRUCTOR':
        is_authorized = Enrollment.objects.filter(
            student=student,
            course__instructor__user=user
        ).exists()
        
    if not is_authorized:
        raise PermissionDenied

    if user.is_superuser or user_role == 'EMPLOYEE' or student.user == user:
        student_submissions = Submission.objects.filter(student=student).select_related('assignment__lesson__course').order_by('-submitted_at')
    elif user_role == 'INROLLER' or user_role == 'INSTRUCTOR':
        instructor_profile = getattr(user, 'instructor_profile', None)
        student_submissions = Submission.objects.filter(
            student=student,
            assignment__lesson__course__instructor=instructor_profile
        ).select_related('assignment__lesson__course').order_by('-submitted_at')
    else:
        student_submissions = Submission.objects.none()

    return render(request, 'students/student_detail.html', {
        'student': student,
        'student_submissions': student_submissions,
    })


@login_required
def student_update(request, pk):
    student = get_object_or_404(Student.objects.select_related('user'), pk=pk)
    user = request.user
    user_role = str(getattr(user, 'role', '')).strip()
    
    if not user.is_superuser and user_role != 'EMPLOYEE' and student.user != user:
        raise PermissionDenied
        
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    saved_student = form.save()

                if user == saved_student.user:
                    update_session_auth_hash(request, saved_student.user)
                    
                messages.success(request, "Your profile specifications updated successfully.")
                
                if user.is_superuser or user_role == 'EMPLOYEE':
                    return redirect('student_list')
                return redirect('student_detail', pk=student.id)
            except Exception as e:
                messages.error(request, "An error occurred while updating the profile. Please try again.")
        else:
            messages.error(request, "Failed to update profile. Please check the errors below.")
    else:
        try:
            form = StudentForm(instance=student, user=request.user)
        except Exception:
            student.profile_picture = None
            form = StudentForm(instance=student, user=request.user)
        
    return render(request, 'students/student_form.html', {'form': form, 'student': student, 'action': 'Edit'})


@login_required
def student_delete(request, pk):
    user_role = str(getattr(request.user, 'role', '')).strip()
    
    if not request.user.is_superuser and user_role != 'EMPLOYEE':
        raise PermissionDenied
        
    student = get_object_or_404(Student.objects.select_related('user'), pk=pk)
    if request.method == 'POST':
        student_name = student.user.username if student.user else f"Student #{student.id}"
        
        if student.user:
            student.user.delete()  
        else:
            student.delete()  
            
        messages.success(request, f"Deleted {student_name} successfully.")
        return redirect('student_list')
    return render(request, 'students/student_confirm_delete.html', {'student': student})
