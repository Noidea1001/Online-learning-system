# instructors/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model, update_session_auth_hash  
from django.db import transaction
from django import forms
from django.db.models import Q, Value  
from django.db.models.functions import Concat
from django.contrib import messages

from .models import Instructor
from .forms import InstructorForm, InstructorUserForm 
from courses.models import Course
from submissions.models import Submission

User = get_user_model()

@login_required
def instructor_create_view(request):
    if not request.user.is_superuser and getattr(request.user, 'role', None) != 'EMPLOYEE':
        raise PermissionDenied
        
    if request.method == 'POST':
        user_form = InstructorUserForm(request.POST)
        instructor_form = InstructorForm(request.POST)
        
        if user_form.is_valid() and instructor_form.is_valid():
            try:
                with transaction.atomic():
                    user = user_form.save(commit=False)
                    user.set_password(user_form.cleaned_data['password'])
                    user.role = 'INSTRUCTOR'
                    # Saving user triggers create_role_profile signal → auto-creates blank Instructor
                    user.save()
                    
                    # Fetch the auto-created Instructor and update it with form data
                    instructor, _ = Instructor.objects.get_or_create(user=user)
                    instructor_data = instructor_form.save(commit=False)
                    instructor.specialty = instructor_data.specialty
                    instructor.experience_years = instructor_data.experience_years
                    instructor.bio = instructor_data.bio
                    instructor.save()
                    
                messages.success(request, f"Faculty profile for '{user.get_full_name() or user.username}' initialized successfully.")
                return redirect('instructor_list')
            except Exception as e:
                import traceback
                traceback.print_exc()
                instructor_form.add_error(None, f"Error: {str(e)}")
    else:
        user_form = InstructorUserForm()
        instructor_form = InstructorForm()
        
    return render(request, 'instructors/instructor_form.html', {
        'user_form': user_form,       
        'form': instructor_form,      
        'instructor': None 
    })

@login_required
def instructor_dashboard(request):
    if not request.user.is_superuser and getattr(request.user, 'role', None) != 'INSTRUCTOR':
        raise PermissionDenied
    return redirect('dashboard_home')


# 3. Faculty Administration Datatable List
@login_required
def instructor_list(request):
    if not request.user.is_superuser and getattr(request.user, 'role', None) != 'EMPLOYEE':
        raise PermissionDenied
        
    search_query = request.GET.get('search', '').strip()
    instructors = Instructor.objects.all().select_related('user') 
    
    if search_query:
        instructors = instructors.annotate(
            full_name=Concat('user__first_name', Value(' '), 'user__last_name'),
            full_name_reverse=Concat('user__last_name', Value(' '), 'user__first_name')
        ).filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(full_name__icontains=search_query) |       
            Q(full_name_reverse__icontains=search_query) 
        )
        
    return render(request, 'instructors/instructor_list.html', {
        'instructors': instructors,
        'search_query': search_query 
    })


# 4. Faculty Profile Information Record Details

@login_required
def instructor_detail(request, pk):
    instructor = get_object_or_404(Instructor, pk=pk)
    user_role = getattr(request.user, 'role', None)
    
    if not request.user.is_superuser and user_role != 'EMPLOYEE' and instructor.user != request.user:
        raise PermissionDenied
        
    courses = Course.objects.filter(instructor=instructor)
    
    return render(request, 'instructors/instructor_detail.html', {
        'instructor': instructor,
        'courses': courses
    })

@login_required
def instructor_update(request, pk):
    instructor = get_object_or_404(Instructor, pk=pk)
    user = instructor.user  
    
    user_role = getattr(request.user, 'role', None)
    if not request.user.is_superuser and user_role != 'EMPLOYEE' and instructor.user != request.user:
        raise PermissionDenied
        
    if request.method == 'POST':
        user_form = InstructorUserForm(request.POST, instance=user)
        instructor_form = InstructorForm(request.POST, instance=instructor)
        
        if 'password' in user_form.fields:
            user_form.fields['password'].required = False
        
        if user_form.is_valid() and instructor_form.is_valid():
            try:
                with transaction.atomic():
                    updated_user = user_form.save(commit=False)
                    
                    if user_form.cleaned_data.get('password'):
                        updated_user.set_password(user_form.cleaned_data['password'])
                        
                    updated_user.save()
                    instructor_form.save()
                
                if request.user == updated_user:
                    update_session_auth_hash(request, updated_user)
                
                messages.success(request, "Faculty profile specifications updated successfully.")
                
                if getattr(request.user, 'role', None) == 'INSTRUCTOR':
                    return redirect('instructor_detail', pk=instructor.id)
                
                if request.user.is_superuser or user_role == 'EMPLOYEE':
                    return redirect('instructor_list')
                    
                return redirect('dashboard_home')
            except Exception as e:
                import traceback
                traceback.print_exc()
                messages.error(request, f"An error occurred while updating. Please try again.")
    else:
        user_form = InstructorUserForm(instance=user)
        instructor_form = InstructorForm(instance=instructor)
        
        if 'password' in user_form.fields:
            user_form.fields['password'].required = False
        
    return render(request, 'instructors/instructor_form.html', {
        'user_form': user_form,
        'form': instructor_form, 
        'instructor': instructor
    })

@login_required
def instructor_delete(request, pk):
    if not request.user.is_superuser and getattr(request.user, 'role', None) != 'EMPLOYEE':
        raise PermissionDenied
        
    instructor = get_object_or_404(Instructor, pk=pk)
    if request.method == 'POST':
        user_name = instructor.user.username
        instructor.user.delete() 
        messages.success(request, f"Permanently wiped out faculty profile record context belonging to @{user_name}.")
        return redirect('instructor_list')
    return render(request, 'instructors/instructor_confirm_delete.html', {'instructor': instructor})
