# submissions/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages  
from django.utils import timezone
from django.db.models import Q # <--- CRITICAL FOR COURSE-WIDE TASKS LOOKUP
from assignments.models import Assignment
from students.models import Student  
from enrollments.models import Enrollment  
from .models import Submission
from .forms import SubmissionForm, GradeForm

def has_submission_permission(user):
    return user.is_authenticated and (user.role == 'INSTRUCTOR' or user.is_lms_admin)

@login_required
def submission_list(request):
    if not has_submission_permission(request.user):
        raise PermissionDenied
        
    if request.user.is_lms_admin:
        # Load both lesson paths and direct course paths for administrators
        submissions = Submission.objects.all().select_related(
            'student__user', 
            'assignment__lesson__course',
            'assignment__course'
        )
    else:
        # FIXED QUERY: Fetch submissions matching instructor's course via a lesson OR direct course mapping
        submissions = Submission.objects.filter(
            Q(assignment__lesson__course__instructor__user=request.user) |
            Q(assignment__course__instructor__user=request.user)
        ).select_related(
            'student__user', 
            'assignment__lesson__course',
            'assignment__course'
        ).order_by('-submitted_at')
        
    return render(request, 'submissions/submission_list.html', {'submissions': submissions})


# submissions/views.py

@login_required
def submission_detail(request, pk):
    submission = get_object_or_404(
        Submission.objects.select_related(
            'student__user', 
            'assignment__lesson__course',
            'assignment__course'
        ), 
        pk=pk
    )
    
    # Check ownership safely for both lesson-bound tasks and course-wide tasks
    is_lesson_owner = (
        submission.assignment.lesson and 
        submission.assignment.lesson.course.instructor.user == request.user
    )
    is_course_owner = (
        submission.assignment.course and 
        submission.assignment.course.instructor.user == request.user
    )
    
    is_owner_instructor = request.user.role == 'INSTRUCTOR' and (is_lesson_owner or is_course_owner)
    
    is_student_owner = request.user.role == 'STUDENT' and submission.student.user == request.user

    if not request.user.is_lms_admin and not is_owner_instructor and not is_student_owner:
        raise PermissionDenied

    form = GradeForm(instance=submission) if (request.user.is_lms_admin or is_owner_instructor) else None
    
    return render(request, 'submissions/submission_detail.html', {
        'submission': submission,
        'form': form
    })




@login_required
def submission_create(request, assignment_id):
    if request.user.role != 'STUDENT': 
        return redirect('dashboard_home')
        
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    if assignment.due_date < timezone.now():
        messages.error(request, "This assignment has already passed its due date.")
        return redirect('student_submissions_dashboard')
        
    try:
        student_profile = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Your student profile setup is incomplete. Please contact support.")
        return redirect('dashboard_home')

    already_submitted = Submission.objects.filter(assignment=assignment, student=student_profile).exists()
    if already_submitted:
        messages.warning(request, f"You have already submitted a response for: '{assignment.title}'.")
        return redirect('student_submissions_dashboard')

    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.student = student_profile  
            submission.save()
            
            # Trigger notification to instructor
            try:
                from notifications.models import Notification
                from django.urls import reverse
                course = assignment.course or (assignment.lesson.course if assignment.lesson else None)
                if course and course.instructor and course.instructor.user:
                    student_name = request.user.get_full_name() or request.user.username
                    Notification.objects.create(
                        recipient=course.instructor.user,
                        sender=request.user,
                        notification_type=Notification.Type.SUBMISSION,
                        title="New Task Submission",
                        message=f"Student {student_name} submitted task '{assignment.title}' for course '{course.title}'.",
                        url=reverse('submission_detail', args=[submission.id])
                    )
            except Exception as e:
                pass

            messages.success(request, f"Assignment '{assignment.title}' submitted successfully!")
            return redirect('student_submissions_dashboard')
        else:
            messages.error(request, "There was an error with your submission form. Please check the file type or size.")
    else:
        form = SubmissionForm()
        
    return render(request, 'submissions/submission_form.html', {
        'form': form, 
        'assignment': assignment
    })


@login_required
def submission_grade(request, pk):
    submission = get_object_or_404(Submission, pk=pk)
    
    is_lesson_owner = (
        submission.assignment.lesson and 
        submission.assignment.lesson.course.instructor.user == request.user
    )
    is_course_owner = (
        submission.assignment.course and 
        submission.assignment.course.instructor.user == request.user
    )
    
    is_owner_instructor = request.user.role == 'INSTRUCTOR' and (is_lesson_owner or is_course_owner)
    
    if not request.user.is_lms_admin and not is_owner_instructor:
        messages.error(request, "You do not have permission to grade this student submission.")
        return redirect('submission_list')

    if request.method == 'POST':
        form = GradeForm(request.POST, instance=submission)
        if form.is_valid():
            assigned_score = form.cleaned_data.get('score')
            max_score = submission.assignment.max_score
            
            if assigned_score is not None and assigned_score > max_score:
                form.add_error('score', f"Score cannot be greater than the maximum score of {max_score}.")
            elif assigned_score is not None and assigned_score < 0:
                form.add_error('score', "Score cannot be less than 0.")
            else:
                form.save()
                student_name = submission.student.user.get_full_name() or submission.student.user.username
                
                # Trigger notification to student
                try:
                    from notifications.models import Notification
                    from django.urls import reverse
                    Notification.objects.create(
                        recipient=submission.student.user,
                        sender=request.user,
                        notification_type=Notification.Type.GRADE,
                        title="Assignment Task Graded",
                        message=f"Your submission for '{submission.assignment.title}' has been graded. Score: {assigned_score} / {max_score}.",
                        url=reverse('submission_detail', args=[submission.id])
                    )
                except Exception as e:
                    pass

                messages.success(request, f"Graded student '{student_name}' successfully!")
                return redirect('submission_detail', pk=submission.id)
        else:
            messages.error(request, "Grading failed. Please verify the input values.")
    else:
        form = GradeForm(instance=submission)
        
    return render(request, 'submissions/grade_form.html', {
        'form': form, 
        'submission': submission
    })


@login_required
def submission_delete(request, pk):
    if not request.user.is_lms_admin:
        raise PermissionDenied
    submission = get_object_or_404(Submission, pk=pk)
    if request.method == 'POST':
        try:
            submission.delete()
        except Exception:
            submission.submitted_file = None
            submission.delete()
        messages.success(request, "Deleted student submission successfully.")
        return redirect('submission_list')
    return render(request, 'submissions/submission_confirm_delete.html', {'submission': submission})


@login_required
def student_submissions_dashboard(request):
    if request.user.role != 'STUDENT':
        raise PermissionDenied
        
    try:
        student_profile = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Your student profile setup is incomplete. Please contact support.")
        return redirect('dashboard_home')

    enrolled_course_ids = Enrollment.objects.filter(
        student=student_profile
    ).values_list('course_id', flat=True)

    # FIXED QUERY: Fetches student items regardless of whether they live on modular lessons or course frameworks
    all_assignments = Assignment.objects.filter(
        Q(lesson__course_id__in=enrolled_course_ids) | Q(course_id__in=enrolled_course_ids)
    ).select_related('lesson__course', 'course').order_by('-due_date')

    submissions_qs = Submission.objects.filter(student=student_profile, assignment__in=all_assignments)
    submissions_dict = {sub.assignment_id: sub for sub in submissions_qs}

    for assignment in all_assignments:
        submission = submissions_dict.get(assignment.id)
        if submission:
            assignment.submission_id = submission.id
            assignment.score = submission.score
            assignment.feedback = submission.feedback
            assignment.submitted_at = submission.submitted_at
            assignment.status = 'GRADED' if submission.score is not None else 'PENDING'
        else:
            assignment.status = 'NOT_SUBMITTED'

    return render(request, 'submissions/student_submissions_dashboard.html', {
        'assignments': all_assignments  
    })
