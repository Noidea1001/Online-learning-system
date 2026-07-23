from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Assignment
from .forms import AssignmentForm
from lessons.models import Lesson
from submissions.models import Submission 
from enrollments.models import Enrollment

def has_assignment_permission(user):
    return user.is_authenticated and (
        user.role == 'INSTRUCTOR' or 
        user.is_lms_admin  
    )

@login_required
def assignment_list(request):
    user_role = str(getattr(request.user, 'role', '')).strip()
    
    if user_role == 'STUDENT':
        return redirect('student_submissions_dashboard')
        
    if not has_assignment_permission(request.user):
        raise PermissionDenied  
        
    if request.user.is_lms_admin:
        assignments = Assignment.objects.all().distinct()
    else:
        assignments = Assignment.objects.filter(course__instructor__user=request.user).distinct()
        
    return render(request, 'assignments/assignment_list.html', {'assignments': assignments})


@login_required
def assignment_create(request):
    if not has_assignment_permission(request.user):
        raise PermissionDenied
        
    initial_lesson_id = request.GET.get('lesson_id')
        
    if request.method == 'POST':
        form = AssignmentForm(
            request.POST, 
            request.FILES, 
            instructor=request.user, 
            is_lms_admin=request.user.is_lms_admin,
            initial_lesson_id=initial_lesson_id  
        )
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.course = form.cleaned_data.get('course')
            assignment.lesson = form.cleaned_data.get('lesson') 
            assignment.save()
            form.save_m2m() 
            
            messages.success(request, f"Task «{assignment.title}» has been created successfully!")
            return redirect('assignment_list')
        else:
            for error_list in form.errors.values():
                for error in error_list:
                    messages.error(request, error)
    else:
        form = AssignmentForm(
            instructor=request.user, 
            is_lms_admin=request.user.is_lms_admin,
            initial_lesson_id=initial_lesson_id
        )

    return render(request, 'assignments/assignment_form.html', {'form': form})


@login_required
def assignment_update(request, pk):
    if not has_assignment_permission(request.user):
        raise PermissionDenied
        
    if request.user.is_lms_admin:
        assignment = get_object_or_404(Assignment, id=pk)
    else:
        assignment = get_object_or_404(Assignment, id=pk, course__instructor__user=request.user)

    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, instance=assignment, instructor=request.user, is_lms_admin=request.user.is_lms_admin)
        if form.is_valid():
            form.save()
            messages.success(request, "Updated assignment successfully.")
            return redirect('assignment_list')
        else:
            for error_list in form.errors.values():
                for error in error_list:
                    messages.error(request, error)
    else:
        form = AssignmentForm(instance=assignment, instructor=request.user, is_lms_admin=request.user.is_lms_admin)

    return render(request, 'assignments/assignment_form.html', {'form': form})
 

@login_required
def assignment_detail(request, pk):
    user = request.user
    user_role = str(getattr(user, 'role', '')).strip()
    
    assignment = get_object_or_404(Assignment.objects.select_related('course', 'lesson__course'), id=pk)
    
    is_authorized = user.is_lms_admin
    
    if user_role == 'INSTRUCTOR':
        is_authorized = Assignment.objects.filter(
            Q(id=pk, lesson__course__instructor__user=user) |
            Q(id=pk, course__instructor__user=user)
        ).exists()
        
    elif user_role == 'STUDENT':
        is_authorized = Enrollment.objects.filter(
            student__user=user,
            course=assignment.course
        ).exists()
        
    if not is_authorized:
        raise PermissionDenied

    user_submission = None
    if user_role == 'STUDENT':
        user_submission = Submission.objects.filter(
            assignment=assignment, 
            student__user=user
        ).first() 

    context = {
        'assignment': assignment,
        'user_submission': user_submission,
    }
    return render(request, 'assignments/assignment_detail.html', context)


@login_required
def assignment_delete(request, pk):
    if not has_assignment_permission(request.user):
        raise PermissionDenied
        
    if request.user.is_lms_admin:
        assignment = get_object_or_404(Assignment, id=pk)
    else:
        assignment = get_object_or_404(Assignment, id=pk, course__instructor__user=request.user)
    
    if request.method == 'POST':
        title = assignment.title
        assignment.delete()
        messages.success(request, f"Deleted assignment «{title}» successfully.")
        return redirect('assignment_list')
        
    return render(request, 'assignments/assignment_confirm_delete.html', {'assignment': assignment})


@login_required
def load_lessons(request):
    if not has_assignment_permission(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
        
    course_id = request.GET.get('course_id')
    if request.user.is_lms_admin:
        lessons = Lesson.objects.filter(course_id=course_id).values('id', 'title')
    else:
        lessons = Lesson.objects.filter(course_id=course_id, course__instructor__user=request.user).values('id', 'title')
    return JsonResponse(list(lessons), safe=False)
