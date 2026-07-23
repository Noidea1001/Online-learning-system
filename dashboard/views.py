# dashboard/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
from courses.models import Course
from enrollments.models import Enrollment
from submissions.models import Submission
from assignments.models import Assignment
from category.models import Category
from lessons.models import Lesson
from reviews.models import Review

User = get_user_model()


def _get_daily_analytics(user_role, user, month=None, year=None):
    """Return daily data for every day in the given month/year.
    Defaults to the current month if not provided."""
    import json, calendar
    from datetime import date, timedelta
    from quizzes.models import QuizAttempt

    now = timezone.now()
    year  = int(year)  if year  else now.year
    month = int(month) if month else now.month

    # All days in the selected month
    num_days = calendar.monthrange(year, month)[1]
    dates  = [date(year, month, d) for d in range(1, num_days + 1)]
    labels = [d.strftime('%b %d') for d in dates]

    daily_enrollments  = []
    daily_test_attempts = []
    daily_test_scores  = []
    daily_submissions  = []

    instructor = getattr(user, 'instructor_profile', None)
    student    = getattr(user, 'student_profile', None)

    for d in dates:
        if user.is_superuser or user_role == 'EMPLOYEE':
            enr_count = Enrollment.objects.filter(enrolled_at__date=d).count()
            sub_count = Submission.objects.filter(submitted_at__date=d).count()
            att_qs    = QuizAttempt.objects.filter(submitted_at__date=d, is_completed=True)
        elif user_role == 'INSTRUCTOR':
            enr_count = Enrollment.objects.filter(course__instructor=instructor, enrolled_at__date=d).count() if instructor else 0
            sub_count = Submission.objects.filter(assignment__course__instructor=instructor, submitted_at__date=d).count() if instructor else 0
            att_qs    = QuizAttempt.objects.filter(quiz__course__instructor=instructor, submitted_at__date=d, is_completed=True) if instructor else QuizAttempt.objects.none()
        else:  # STUDENT
            enr_count = Enrollment.objects.filter(student=student, enrolled_at__date=d).count() if student else 0
            sub_count = Submission.objects.filter(student=student, submitted_at__date=d).count() if student else 0
            att_qs    = QuizAttempt.objects.filter(student=student, submitted_at__date=d, is_completed=True) if student else QuizAttempt.objects.none()

        daily_enrollments.append(enr_count)
        daily_submissions.append(sub_count)
        att_count = att_qs.count()
        daily_test_attempts.append(att_count)
        avg = att_qs.filter(score__isnull=False).aggregate(avg=Avg('score'))['avg']
        daily_test_scores.append(float(round(avg, 1)) if avg is not None else 0)

    return {
        'daily_labels_json':        json.dumps(labels),
        'daily_enrollments_json':   json.dumps(daily_enrollments),
        'daily_submissions_json':   json.dumps(daily_submissions),
        'daily_test_attempts_json': json.dumps(daily_test_attempts),
        'daily_test_scores_json':   json.dumps(daily_test_scores),
    }


@login_required
def dashboard_analytics_api(request):
    """AJAX endpoint — returns filtered daily analytics as JSON.
    Query params: ?month=7&year=2026"""
    from django.http import JsonResponse
    user      = request.user
    user_role = str(getattr(user, 'role', '')).strip()
    month     = request.GET.get('month')
    year      = request.GET.get('year')
    data      = _get_daily_analytics(user_role, user, month=month, year=year)

    import json
    return JsonResponse({
        'labels':       json.loads(data['daily_labels_json']),
        'enrollments':  json.loads(data['daily_enrollments_json']),
        'submissions':  json.loads(data['daily_submissions_json']),
        'testAttempts': json.loads(data['daily_test_attempts_json']),
        'testScores':   json.loads(data['daily_test_scores_json']),
    })


@login_required
def dashboard_home(request):
    user = request.user
    context = {}
    now = timezone.now()
    user_role = str(getattr(user, 'role', '')).strip()

    daily_data = _get_daily_analytics(user_role, user)
    context.update(daily_data)

    # for admin
    if user.is_superuser or user_role == 'EMPLOYEE':
        from students.models import Student
        from instructors.models import Instructor
        from employees.models import Employee

        total_courses = Course.objects.count()
     
        total_published = Course.objects.filter(is_published=True).count()
        
        
        published_percentage = (total_published / total_courses * 100) if total_courses > 0 else 0

        total_enrollments = Enrollment.objects.count()
        total_paid_enrollments = Enrollment.objects.filter(is_paid=True).count()

        from quizzes.models import Quiz, QuizAttempt
        completed_attempts = QuizAttempt.objects.filter(is_completed=True)
        avg_test_score = completed_attempts.filter(score__isnull=False).aggregate(avg=Avg('score'))['avg']

        context.update({
            # System-wide Statistics
            'total_users':       User.objects.count(),
            'total_students':    Student.objects.count(),
            'total_instructors': Instructor.objects.count(),
            'total_employees':   Employee.objects.count(),
            'total_courses':     total_courses,
            'total_published':   total_published,  
            'published_percentage': published_percentage,  
            'total_categories':  Category.objects.count(),
            'total_lessons':     Lesson.objects.count(),
            'total_assignments': Assignment.objects.count(),
            'total_submissions': Submission.objects.count(),
            'total_enrollments': total_enrollments,
            'total_paid_enrollments': total_paid_enrollments,
            'total_unpaid_enrollments': max(0, total_enrollments - total_paid_enrollments),
            'total_unenrolled_students': Student.objects.filter(enrollments__isnull=True).count(),
            'pending_reviews_count': Review.objects.filter(is_approved=False).count(),

            # Test / quiz activity
            'total_tests': Quiz.objects.filter(status='PUBLISHED').count(),
            'total_test_attempts': completed_attempts.count(),
            'avg_test_score': float(round(avg_test_score, 1)) if avg_test_score is not None else None,
            'pending_test_grading': QuizAttempt.objects.filter(needs_grading=True).count(),
            'recent_test_attempts': completed_attempts.select_related(
                'quiz__course', 'student__user'
            ).order_by('-submitted_at')[:6],

            # Recent Activity Logs
            'recent_enrollments': Enrollment.objects.select_related(
                'student__user', 'course'
            ).order_by('-enrolled_at')[:6],
            
            'recent_courses': Course.objects.select_related(
                'instructor__user', 'category'
            ).order_by('-created_at')[:5],
            
            'recent_submissions': Submission.objects.select_related(
                'student__user', 'assignment__lesson__course'
            ).order_by('-submitted_at')[:5],
        })

#  INSTRUCTOR DASHBOARD (My Courses, Enrollment, Progress & Grading)
    elif user_role == 'INSTRUCTOR':
            instructor = user.instructor_profile
            
            my_courses = Course.objects.filter(instructor=instructor).select_related('category').order_by('-created_at')
            
            course_stats = my_courses.annotate(
                student_count=Count('enrollments', distinct=True),
                avg_rating=Avg('reviews__rating')
            )
            
            course_counts = my_courses.aggregate(
                total=Count('id'),
                published=Count('id', filter=Q(is_published=True)),
                draft=Count('id', filter=Q(is_published=False))
            )
            
            my_courses_count = course_counts['total']
            total_published = course_counts['published']
            my_draft_count = course_counts['draft']
            
            my_enrollments = Enrollment.objects.filter(course__instructor=instructor).select_related('student__user', 'course')
            my_students_count = my_enrollments.values('student').distinct().count()
            
            my_paid_enrollments = my_enrollments.filter(is_paid=True).count()
            
            pending_submissions = Submission.objects.filter(
                assignment__course__instructor=instructor,
                score__isnull=True
            ).select_related('student__user', 'assignment__course').order_by('-submitted_at')
            
            pending_count = pending_submissions.count()
            
            # calculate the percentage
            published_percentage = (total_published / my_courses_count * 100) if my_courses_count > 0 else 0

            from quizzes.models import Quiz, QuizAttempt
            my_tests = Quiz.objects.filter(course__instructor=instructor)
            my_test_attempts = QuizAttempt.objects.filter(quiz__course__instructor=instructor, is_completed=True)
            my_avg_test_score = my_test_attempts.filter(score__isnull=False).aggregate(avg=Avg('score'))['avg']

            context.update({
                'instructor': instructor,
                'my_courses': my_courses,
                'enrolled_students': my_enrollments.order_by('-enrolled_at')[:10],
                'pending_submissions': pending_submissions,
                
                'pending_submissions_count': pending_count,
                'my_pending_count':          pending_count, 
                
                'course_stats': course_stats,
                
                # data-attributes of JavaScript Turn
                'my_courses_count':       my_courses_count,
                'my_published_count':     total_published,  
                'my_students_count':      my_students_count,
                'my_paid_enrollments':    my_paid_enrollments,
                
                # data for Template
                'total_courses':          my_courses_count,
                'my_draft_count':         my_draft_count,
                'published_percentage':   published_percentage,

                # Test / quiz activity
                'my_tests_count': my_tests.filter(status='PUBLISHED').count(),
                'my_test_attempts_count': my_test_attempts.count(),
                'my_avg_test_score': round(my_avg_test_score, 1) if my_avg_test_score is not None else None,
                'my_pending_test_grading': QuizAttempt.objects.filter(
                    quiz__course__instructor=instructor, needs_grading=True
                ).count(),
                'recent_test_attempts': my_test_attempts.select_related(
                    'quiz', 'student__user'
                ).order_by('-submitted_at')[:6],
            })


    # ── 3. STUDENT DASHBOARD (Enrollments, Progress, Deadlines & Grades)
   
    elif user_role == 'STUDENT':
        student = user.student_profile
    
        enrollments = Enrollment.objects.filter(student=student).select_related(
            'course__instructor__user', 'course__category'
        ).annotate(
            total_lessons_count=Count('course__lessons', distinct=True),
            completed_lessons_count=Count('completed_lessons', distinct=True)
        ).order_by('-enrolled_at')
        
        for enrollment in enrollments:
            total = enrollment.total_lessons_count
            completed = enrollment.completed_lessons_count
            enrollment.calculated_progress = int((completed / total) * 100) if total > 0 else 0

        enrolled_course_ids = enrollments.values_list('course_id', flat=True)
        submitted_assignment_ids = Submission.objects.filter(student=student).values_list('assignment_id', flat=True)
        
        upcoming_assignments = Assignment.objects.filter(
            lesson__course_id__in=enrolled_course_ids,
            due_date__gt=now
        ).exclude(id__in=submitted_assignment_ids).select_related('lesson__course').order_by('due_date')[:5]

        my_submissions = Submission.objects.filter(student=student).select_related('assignment__lesson__course').order_by('-submitted_at')
        my_reviews = Review.objects.filter(student=student).select_related('course').order_by('-created_at')

        enrollment_stats = enrollments.aggregate(
            total=Count('id'),
            paid=Count('id', filter=Q(is_paid=True)),
            free=Count('id', filter=Q(course__price__lte=0))
        )
        submission_stats = my_submissions.aggregate(
            total=Count('id'),
            graded=Count('id', filter=Q(score__isnull=False)),
            pending=Count('id', filter=Q(score__isnull=True))
        )
        available_free_courses = Course.objects.filter(price__lte=0, is_published=True).count()

        from quizzes.models import Quiz, QuizAttempt
        my_test_attempts = QuizAttempt.objects.filter(student=student, is_completed=True)
        my_avg_test_score = my_test_attempts.filter(score__isnull=False).aggregate(avg=Avg('score'))['avg']
        available_tests_count = Quiz.objects.filter(
            course_id__in=enrolled_course_ids, status='PUBLISHED'
        ).count()

        context.update({
            'instructor':               None,
            'my_enrollments':           enrollments,
            'upcoming_assignments':     upcoming_assignments,
            'my_submissions':           my_submissions[:5],
            'my_reviews':               my_reviews,
            'total_submissions':        submission_stats['graded'],     
            'total_assignments':        submission_stats['total'], 
            
            # HTML Data-Attributes
            'my_enrollments_count':     enrollment_stats['total'],       
            'my_paid_count':            enrollment_stats['paid'],    
            'available_courses_count':  available_free_courses,   
            'my_submissions_count':     submission_stats['total'],
            'my_graded_count':          submission_stats['graded'],
            'my_pending_count':         submission_stats['pending'],

            # Test / quiz activity
            'my_test_attempts_count': my_test_attempts.count(),
            'my_avg_test_score': round(my_avg_test_score, 1) if my_avg_test_score is not None else None,
            'available_tests_count': available_tests_count,
            'recent_test_attempts': my_test_attempts.select_related('quiz__course').order_by('-submitted_at')[:6],
        })

    return render(request, 'dashboard/home.html', context)


@login_required
def calendar_view(request):
    """Interactive calendar showing assignment due dates and quiz deadlines."""
    import json
    from datetime import datetime
    from django.urls import reverse
    from quizzes.models import Quiz, QuizAttempt

    user = request.user
    now = timezone.now()
    events = []

    user_role = str(getattr(user, 'role', '')).strip()

    if user_role == 'STUDENT':
        student = user.student_profile
        enrolled_course_ids = Enrollment.objects.filter(student=student).values_list('course_id', flat=True)

        # Assignment events
        submitted_map = {}
        for sub in Submission.objects.filter(student=student).select_related('assignment'):
            submitted_map[sub.assignment_id] = sub

        assignments = Assignment.objects.filter(
            Q(course_id__in=enrolled_course_ids) | Q(lesson__course_id__in=enrolled_course_ids)
        ).select_related('course', 'lesson__course')

        for a in assignments:
            course = a.course or (a.lesson.course if a.lesson else None)
            sub = submitted_map.get(a.id)
            if sub:
                if sub.score is not None:
                    status = 'graded'
                else:
                    status = 'submitted'
            elif a.due_date and a.due_date < now:
                status = 'overdue'
            else:
                status = 'pending'

            event_url = ''
            try:
                if sub:
                    event_url = reverse('submission_detail', args=[sub.id])
                elif status == 'pending' or status == 'overdue':
                    event_url = reverse('submission_create', args=[a.id])
            except Exception:
                pass

            events.append({
                'id': f'a-{a.id}',
                'title': a.title,
                'date': a.due_date.strftime('%Y-%m-%d') if a.due_date else '',
                'time': a.due_date.strftime('%H:%M') if a.due_date else '',
                'type': 'assignment',
                'course': course.title if course else 'Unknown',
                'status': status,
                'score': f'{sub.score}/{a.max_score}' if sub and sub.score is not None else '',
                'url': event_url,
                'max_score': str(a.max_score),
            })

        # Quiz events
        quizzes = Quiz.objects.filter(
            course_id__in=enrolled_course_ids,
            status='PUBLISHED',
            due_date__isnull=False,
        ).select_related('course')

        for q in quizzes:
            attempt = QuizAttempt.objects.filter(quiz=q, student=student, is_completed=True).first()
            if attempt:
                if attempt.score is not None:
                    status = 'graded'
                else:
                    status = 'submitted'
            elif q.due_date and q.due_date < now:
                status = 'overdue'
            else:
                status = 'pending'

            event_url = ''
            try:
                if attempt:
                    event_url = reverse('quiz_result', args=[attempt.id])
                else:
                    event_url = reverse('quiz_take', args=[q.id])
            except Exception:
                pass

            events.append({
                'id': f'q-{q.id}',
                'title': q.title,
                'date': q.due_date.strftime('%Y-%m-%d') if q.due_date else '',
                'time': q.due_date.strftime('%H:%M') if q.due_date else '',
                'type': 'quiz',
                'course': q.course.title if q.course else 'Unknown',
                'status': status,
                'score': f'{attempt.score}%' if attempt and attempt.score is not None else '',
                'url': event_url,
                'max_score': '',
            })

    elif user_role == 'INSTRUCTOR':
        instructor = user.instructor_profile
        my_course_ids = Course.objects.filter(instructor=instructor).values_list('id', flat=True)

        assignments = Assignment.objects.filter(
            Q(course_id__in=my_course_ids) | Q(lesson__course_id__in=my_course_ids)
        ).select_related('course', 'lesson__course')

        for a in assignments:
            course = a.course or (a.lesson.course if a.lesson else None)
            sub_count = Submission.objects.filter(assignment=a).count()
            pending = Submission.objects.filter(assignment=a, score__isnull=True).count()
            if a.due_date and a.due_date < now:
                status = 'overdue'
            elif pending > 0:
                status = 'submitted'
            else:
                status = 'pending'

            event_url = ''
            try:
                event_url = reverse('submission_list')
            except Exception:
                pass

            events.append({
                'id': f'a-{a.id}',
                'title': a.title,
                'date': a.due_date.strftime('%Y-%m-%d') if a.due_date else '',
                'time': a.due_date.strftime('%H:%M') if a.due_date else '',
                'type': 'assignment',
                'course': course.title if course else 'Unknown',
                'status': status,
                'score': f'{sub_count} submissions ({pending} pending)' if sub_count else 'No submissions',
                'url': event_url,
                'max_score': str(a.max_score),
            })

        quizzes = Quiz.objects.filter(
            course_id__in=my_course_ids,
            status='PUBLISHED',
            due_date__isnull=False,
        ).select_related('course')

        for q in quizzes:
            attempt_count = QuizAttempt.objects.filter(quiz=q, is_completed=True).count()
            pending_grading = QuizAttempt.objects.filter(quiz=q, needs_grading=True).count()
            if q.due_date and q.due_date < now:
                status = 'overdue'
            elif pending_grading > 0:
                status = 'submitted'
            else:
                status = 'pending'

            event_url = ''
            try:
                event_url = reverse('quiz_detail', args=[q.id])
            except Exception:
                pass

            events.append({
                'id': f'q-{q.id}',
                'title': q.title,
                'date': q.due_date.strftime('%Y-%m-%d') if q.due_date else '',
                'time': q.due_date.strftime('%H:%M') if q.due_date else '',
                'type': 'quiz',
                'course': q.course.title if q.course else 'Unknown',
                'status': status,
                'score': f'{attempt_count} attempts ({pending_grading} pending)' if attempt_count else 'No attempts',
                'url': event_url,
                'max_score': '',
            })

    else:
        # Admin/Employee: show all assignments and quizzes
        assignments = Assignment.objects.all().select_related('course', 'lesson__course')
        for a in assignments:
            course = a.course or (a.lesson.course if a.lesson else None)
            event_url = ''
            try:
                event_url = reverse('submission_list')
            except Exception:
                pass

            events.append({
                'id': f'a-{a.id}',
                'title': a.title,
                'date': a.due_date.strftime('%Y-%m-%d') if a.due_date else '',
                'time': a.due_date.strftime('%H:%M') if a.due_date else '',
                'type': 'assignment',
                'course': course.title if course else 'Unknown',
                'status': 'pending' if (a.due_date and a.due_date > now) else 'overdue',
                'score': '',
                'url': event_url,
                'max_score': str(a.max_score),
            })

        quizzes = Quiz.objects.filter(status='PUBLISHED', due_date__isnull=False).select_related('course')
        for q in quizzes:
            event_url = ''
            try:
                event_url = reverse('quiz_detail', args=[q.id])
            except Exception:
                pass

            events.append({
                'id': f'q-{q.id}',
                'title': q.title,
                'date': q.due_date.strftime('%Y-%m-%d') if q.due_date else '',
                'time': q.due_date.strftime('%H:%M') if q.due_date else '',
                'type': 'quiz',
                'course': q.course.title if q.course else 'Unknown',
                'status': 'pending' if (q.due_date and q.due_date > now) else 'overdue',
                'score': '',
                'url': event_url,
                'max_score': '',
            })

    context = {
        'events_json': json.dumps(events),
        'today': now.strftime('%Y-%m-%d'),
        'current_year': now.year,
        'current_month': now.month,
    }
    return render(request, 'dashboard/calendar.html', context)