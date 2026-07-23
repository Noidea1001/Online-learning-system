# lessons/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .models import Lesson
from .forms import LessonForm
from enrollments.models import Enrollment
from courses.models import Course

@login_required
def lesson_create(request):
    if not request.user.is_superuser and request.user.role not in ['INSTRUCTOR', 'EMPLOYEE']:
        raise PermissionDenied
        
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            lesson = form.save()
            messages.success(request, f"Lesson «{lesson.title}» has been created successfully.")
            return redirect('course_detail', pk=lesson.course.pk)
    else:
        course_id = request.GET.get('course')
        initial_data = {}
        
        if course_id:
            course = get_object_or_404(Course, id=course_id)
            
            if request.user.role == 'INSTRUCTOR' and course.instructor != getattr(request.user, 'instructor_profile', None):
                raise PermissionDenied
                
            initial_data['course'] = course
            
        form = LessonForm(user=request.user, initial={**initial_data, **request.GET.dict()})
        
    return render(request, 'lessons/lesson_form.html', {'form': form, 'action': 'Add'})


@login_required
def lesson_list(request):
    user = request.user
    
    if not user.is_superuser and user.role not in ['EMPLOYEE', 'INSTRUCTOR']:
        raise PermissionDenied
        
    if user.is_superuser or user.role == 'EMPLOYEE':
        lessons = Lesson.objects.all().select_related('course')
    elif user.role == 'INSTRUCTOR':
        instructor_profile = getattr(user, 'instructor_profile', None)
        lessons = Lesson.objects.filter(course__instructor=instructor_profile).select_related('course')
        
    return render(request, 'lessons/lesson_list.html', {'lessons': lessons})


@login_required
def lesson_update(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    
    if not request.user.is_superuser and request.user.role != 'EMPLOYEE':
        instructor_profile = getattr(request.user, 'instructor_profile', None)
        if lesson.course.instructor != instructor_profile:
            raise PermissionDenied
            
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, instance=lesson, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Lesson «{lesson.title}» has been updated successfully.")
            return redirect('lesson_detail', pk=lesson.pk)
    else:
        form = LessonForm(instance=lesson, user=request.user)
        
    return render(request, 'lessons/lesson_form.html', {'form': form, 'action': 'Edit', 'lesson': lesson})


@login_required
def lesson_delete(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    
    if not request.user.is_superuser and request.user.role != 'EMPLOYEE' and lesson.course.instructor != getattr(request.user, 'instructor_profile', None):
        raise PermissionDenied
        
    course_pk = lesson.course.pk
    if request.method == 'POST':
        lesson_title = lesson.title
        lesson.delete()
        messages.success(request, f"Lesson «{lesson_title}» has been deleted successfully.")
        return redirect('course_detail', pk=course_pk)
    return render(request, 'lessons/lesson_confirm_delete.html', {'lesson': lesson})


@login_required
def lesson_detail(request, pk):
    lesson = get_object_or_404(
        Lesson.objects.select_related('course__instructor').prefetch_related('assignments'), 
        pk=pk
    )
    
    is_enrolled = False
    is_completed = False
    
    if request.user.is_superuser or request.user.role == 'EMPLOYEE':
        is_enrolled = True
    elif request.user.role == 'INSTRUCTOR' and lesson.course.instructor == getattr(request.user, 'instructor_profile', None):
        is_enrolled = True
    else:
        course_is_free = getattr(lesson.course, 'is_free', False)
        course_price = getattr(lesson.course, 'price', 0) or 0

        if course_is_free or course_price <= 0:
            is_enrolled = True
        
        if request.user.role == 'STUDENT' and hasattr(request.user, 'student_profile'):
            enrollment_qs = Enrollment.objects.filter(student=request.user.student_profile, course=lesson.course)
            if enrollment_qs.exists():
                enrollment = enrollment_qs.first()
                if enrollment.is_paid or course_is_free or course_price <= 0:
                    is_enrolled = True
                    is_completed = enrollment.completed_lessons.filter(id=lesson.id).exists()
                else:
                    messages.warning(request, "You must pay for this course to view its lessons.")
                    return redirect('course_detail', pk=lesson.course.pk)
            else:
                is_enrolled = False

    if not is_enrolled:
        messages.warning(request, "You must be enrolled in this course to view its lessons.")
        return redirect('course_detail', pk=lesson.course.pk)
            
    if request.user.role == 'STUDENT' and hasattr(request.user, 'student_profile'):
        from submissions.models import Submission
        
        submitted_assignment_ids = Submission.objects.filter(
            assignment__lesson=lesson,
            student=request.user.student_profile
        ).values_list('assignment_id', flat=True)
        
        for assignment in lesson.assignments.all():
            assignment.user_has_submitted = assignment.id in submitted_assignment_ids

    return render(request, 'lessons/lesson_detail.html', {
        'lesson': lesson,
        'is_enrolled': is_enrolled,
        'is_completed': is_completed,
    })


@login_required
def toggle_lesson_completion(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    if request.user.role != 'STUDENT' or not hasattr(request.user, 'student_profile'):
        raise PermissionDenied
    
    enrollment = get_object_or_404(Enrollment, student=request.user.student_profile, course=lesson.course)
    
    if request.method == 'POST':
        if enrollment.completed_lessons.filter(id=lesson.id).exists():
            enrollment.completed_lessons.remove(lesson)
            messages.success(request, f"Removed '{lesson.title}' from completed lessons.")
        else:
            enrollment.completed_lessons.add(lesson)
            messages.success(request, f"Marked '{lesson.title}' as completed!")
            
    return redirect('lesson_detail', pk=lesson.id)
