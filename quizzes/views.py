# quizzes/views.py
import csv
import json
import random
import string

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from courses.models import Course
from enrollments.models import Enrollment
from students.models import Student

from .models import Choice, Question, QuestionBankChoice, QuestionBankItem, Quiz, QuizAttempt, StudentAnswer


def has_quiz_permission(user):
    """Only instructors and LMS admins (superusers/employees) can build tests."""
    return user.is_authenticated and (user.role == 'INSTRUCTOR' or user.is_lms_admin)


def _scoped_quiz_or_404(request, pk):
    """Fetch a quiz the current staff user is allowed to manage — instructors
    only ever get their own courses' tests, admins/employees get everything."""
    if request.user.is_lms_admin:
        return get_object_or_404(Quiz.objects.select_related('course', 'lesson'), pk=pk)
    return get_object_or_404(
        Quiz.objects.select_related('course', 'lesson'), pk=pk, course__instructor__user=request.user
    )


# ──────────────────────────────────────────────────────────
#  STAFF: LIST / BUILD / DETAIL / DELETE / DUPLICATE
# ──────────────────────────────────────────────────────────
@login_required
def quiz_list(request):
    if request.user.role == 'STUDENT':
        return redirect('student_quiz_list')
    if not has_quiz_permission(request.user):
        raise PermissionDenied

    if request.user.is_lms_admin:
        quizzes = Quiz.objects.select_related('course', 'lesson').all()
    else:
        quizzes = Quiz.objects.select_related('course', 'lesson').filter(course__instructor__user=request.user)

    search_query = request.GET.get('search', '').strip()
    if search_query:
        quizzes = quizzes.filter(
            models.Q(title__icontains=search_query) | models.Q(course__title__icontains=search_query)
        )

    paginator = Paginator(quizzes, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'quizzes/quiz_list.html', {
        'quizzes': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search_query': search_query,
    })


def _builder_field_values(quiz, form_state=None):
    """
    Builds a plain dict of initial form values for the builder template.

    This exists specifically to avoid a Django template gotcha: something
    like `{{ form_state.title|default:quiz.title|default:'' }}` looks safe,
    but `quiz.title` there is a *filter argument*, not the main filtered
    value — and Django does NOT suppress VariableDoesNotExist for filter
    arguments the way it does for the main value. So when `quiz` is None
    (creating a new test), `quiz.title` as an argument raises instead of
    quietly resolving to nothing, crashing the whole page. Resolving
    everything here in Python, where a None-check is trivial, sidesteps
    the whole class of bug — the template only ever does a plain dict
    lookup on a dict that's guaranteed to exist.
    """
    defaults = {
        'title': '', 'description': '', 'time_limit_minutes': '',
        'max_attempts': 1, 'passing_score': '', 'course': '',
    }
    if form_state is not None:
        return {key: form_state.get(key, default) for key, default in defaults.items()}
    if quiz is not None:
        values = {}
        for key, default in defaults.items():
            if key == 'course':
                values[key] = str(quiz.course_id) if quiz.course_id else default
                continue
            value = getattr(quiz, key, None)
            values[key] = value if value not in (None, '') else default
        return values
    return defaults


@login_required
def quiz_builder(request, pk=None):
    if not has_quiz_permission(request.user):
        raise PermissionDenied

    quiz = _scoped_quiz_or_404(request, pk) if pk else None

    # Tests that already have student attempts are locked from question
    # edits — rebuilding the question set would silently invalidate real
    # student answers. Duplicate instead.
    if quiz and quiz.has_attempts:
        messages.error(
            request,
            f"«{quiz.title}» already has student attempts, so its questions are locked. "
            f"Duplicate it to make changes."
        )
        return redirect('quiz_detail', pk=quiz.pk)

    if request.user.is_lms_admin:
        courses = Course.objects.all().order_by('title')
    else:
        courses = Course.objects.filter(instructor__user=request.user).order_by('title')

    if request.method == 'POST':
        action = request.POST.get('action', 'draft')
        course_id = request.POST.get('course')
        lesson_id = request.POST.get('lesson') or None
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        time_limit = request.POST.get('time_limit_minutes') or None
        max_attempts = request.POST.get('max_attempts') or 1
        passing_score = request.POST.get('passing_score') or None
        shuffle = request.POST.get('shuffle_questions') == 'on'
        due_date = request.POST.get('due_date') or None
        questions_json = request.POST.get('questions_json', '[]')

        try:
            questions_data = json.loads(questions_json)
            if not isinstance(questions_data, list):
                questions_data = []
        except (ValueError, TypeError):
            questions_data = []

        course = courses.filter(pk=course_id).first()

        lesson = None
        if course and lesson_id:
            lesson = course.lessons.filter(pk=lesson_id).first()
            if lesson is None:
                lesson_id = None

        error = None
        if not title:
            error = "Please give the test a title."
        elif not course:
            error = "Please choose a valid course."
        elif action == 'publish' and not questions_data:
            error = "Add at least one question before publishing."
        elif action == 'publish':
            for q in questions_data:
                choices = q.get('choices') or []
                if not q.get('text', '').strip():
                    error = "Every question needs text before publishing."
                    break
                if q.get('type') == 'SHORT_ANSWER':
                    continue
                if len(choices) < 2:
                    error = f'"{q.get("text", "Untitled question")[:40]}" needs at least 2 answer options.'
                    break
                if not any(c.get('is_correct') for c in choices):
                    error = f'"{q.get("text", "Untitled question")[:40]}" needs a correct answer marked.'
                    break

        if error:
            messages.error(request, error)
            return render(request, 'quizzes/quiz_builder.html', {
                'quiz': quiz,
                'courses': courses,
                'initial_questions': questions_data,
                'field_values': _builder_field_values(quiz, form_state=request.POST),
            })

        if quiz is None:
            quiz = Quiz(created_by=request.user)

        quiz.course = course
        quiz.lesson = lesson
        quiz.title = title
        quiz.description = description
        quiz.time_limit_minutes = time_limit or None
        quiz.max_attempts = int(max_attempts) if str(max_attempts).isdigit() else 1
        quiz.passing_score = passing_score or None
        quiz.shuffle_questions = shuffle
        quiz.due_date = due_date or None
        quiz.status = Quiz.Status.PUBLISHED if action == 'publish' else Quiz.Status.DRAFT
        quiz.save()

        # Full rebuild of the question set — safe here since we already
        # blocked this path above whenever attempts exist.
        quiz.questions.all().delete()
        for q_order, q in enumerate(questions_data):
            if not q.get('text', '').strip():
                continue
            question = Question.objects.create(
                quiz=quiz,
                order=q_order,
                text=q.get('text', '').strip(),
                question_type=q.get('type') or Question.Type.SINGLE,
                points=int(q.get('points') or 1),
                sample_answer=(q.get('sample_answer') or '').strip(),
            )
            for c_order, c in enumerate(q.get('choices') or []):
                if not c.get('text', '').strip():
                    continue
                Choice.objects.create(
                    question=question,
                    order=c_order,
                    text=c.get('text', '').strip(),
                    is_correct=bool(c.get('is_correct')),
                )

        status_label = 'published' if quiz.status == Quiz.Status.PUBLISHED else 'saved as a draft'
        messages.success(request, f"Test «{quiz.title}» {status_label}.")
        return redirect('quiz_list')

    # GET — hydrate the JS builder with existing questions, if editing.
    initial_questions = []
    if quiz:
        for q in quiz.questions.prefetch_related('choices').all():
            initial_questions.append({
                'text': q.text,
                'type': q.question_type,
                'points': q.points,
                'sample_answer': q.sample_answer,
                'choices': [{'text': c.text, 'is_correct': c.is_correct} for c in q.choices.all()],
            })

    field_values = _builder_field_values(quiz)
    if quiz is None and request.GET.get('course'):
        preselect = courses.filter(pk=request.GET.get('course')).first()
        if preselect:
            field_values['course'] = str(preselect.id)

    return render(request, 'quizzes/quiz_builder.html', {
        'quiz': quiz,
        'courses': courses,
        'initial_questions': initial_questions,
        'field_values': field_values,
    })


@login_required
def quiz_detail(request, pk):
    if not has_quiz_permission(request.user):
        raise PermissionDenied
    quiz = _scoped_quiz_or_404(request, pk)
    attempts = quiz.attempts.filter(is_completed=True).select_related('student__user').order_by('-submitted_at')

    status_filter = request.GET.get('status', 'all')
    if status_filter == 'passed' and quiz.passing_score is not None:
        attempts = attempts.filter(needs_grading=False, score__gte=quiz.passing_score)
    elif status_filter == 'failed' and quiz.passing_score is not None:
        attempts = attempts.filter(needs_grading=False, score__lt=quiz.passing_score)
    elif status_filter == 'pending':
        attempts = attempts.filter(needs_grading=True)
    # 'all' (default) — no extra filtering.

    question_stats = []
    for question in quiz.questions.prefetch_related('choices').all():
        answers = StudentAnswer.objects.filter(question=question, attempt__is_completed=True)
        answered = answers.count()
        full_credit = answers.filter(is_correct=True).count()
        partial_credit = answers.filter(is_correct=False, points_earned__gt=0).count()
        zero_credit = answered - full_credit - partial_credit
        avg_points = answers.aggregate(avg=models.Avg('points_earned'))['avg']

        question_stats.append({
            'question': question,
            'answered': answered,
            'full_credit': full_credit,
            'partial_credit': partial_credit,
            'zero_credit': zero_credit,
            'pct_correct': round((full_credit / answered) * 100, 1) if answered else None,
            'avg_points': round(avg_points, 2) if avg_points is not None else None,
        })

    scored_questions = [q for q in question_stats if q['pct_correct'] is not None]
    toughest_question = min(scored_questions, key=lambda q: q['pct_correct']) if scored_questions else None

    chart_data = [
        {
            'label': (q['question'].text[:45] + '…') if len(q['question'].text) > 45 else q['question'].text,
            'pct': q['pct_correct'] if q['pct_correct'] is not None else 0,
        }
        for q in question_stats
    ]

    return render(request, 'quizzes/quiz_detail.html', {
        'quiz': quiz,
        'attempts': attempts,
        'question_stats': question_stats,
        'toughest_question': toughest_question,
        'chart_data': chart_data,
        'chart_height': max(180, len(question_stats) * 45 + 40),
        'status_filter': status_filter,
    })


@login_required
def quiz_export_results(request, pk):
    """Downloads completed attempts for this test as a CSV — for gradebooks
    or reporting outside the platform."""
    if not has_quiz_permission(request.user):
        raise PermissionDenied
    quiz = _scoped_quiz_or_404(request, pk)

    attempts = (
        quiz.attempts.filter(is_completed=True)
        .select_related('student__user')
        .order_by('student__user__username', '-submitted_at')
    )

    response = HttpResponse(content_type='text/csv')
    safe_title = ''.join(c if c.isalnum() or c in ' -_' else '' for c in quiz.title).strip() or 'test'
    response['Content-Disposition'] = f'attachment; filename="{safe_title} - results.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Student', 'Username', 'Score (%)', 'Result', 'Points Earned', 'Total Points',
        'Submitted At', 'Auto-Submitted (Time Expired)',
    ])

    total_points = quiz.total_points
    for attempt in attempts:
        if attempt.passed is None:
            result = 'N/A'
        else:
            result = 'Passed' if attempt.passed else 'Failed'

        points_earned = round((attempt.score / 100) * total_points, 2) if attempt.score is not None else ''

        writer.writerow([
            attempt.student.user.get_full_name() or attempt.student.user.username,
            attempt.student.user.username,
            attempt.score if attempt.score is not None else '',
            result,
            points_earned,
            total_points,
            attempt.submitted_at.strftime('%Y-%m-%d %H:%M') if attempt.submitted_at else '',
            'Yes' if attempt.is_auto_submitted else 'No',
        ])

    return response


@login_required
def quiz_grade_queue(request, pk):
    """Lists every ungraded short-answer response for this test so an
    instructor can review and score them by hand."""
    if not has_quiz_permission(request.user):
        raise PermissionDenied
    quiz = _scoped_quiz_or_404(request, pk)

    pending_answers = (
        StudentAnswer.objects
        .filter(question__quiz=quiz, question__question_type=Question.Type.SHORT_ANSWER,
                is_graded=False, attempt__is_completed=True)
        .select_related('attempt__student__user', 'question')
        .order_by('attempt__submitted_at', 'question__order')
    )

    return render(request, 'quizzes/quiz_grade_queue.html', {
        'quiz': quiz,
        'pending_answers': pending_answers,
    })


@login_required
def quiz_grade_answer(request, answer_id):
    """Awards points to a single short-answer response and recalculates
    that attempt's overall score once graded."""
    if not has_quiz_permission(request.user):
        raise PermissionDenied
    if request.method != 'POST':
        raise PermissionDenied

    answer = get_object_or_404(
        StudentAnswer.objects.select_related('attempt__quiz__course', 'question'), pk=answer_id
    )
    quiz = answer.attempt.quiz
    if not request.user.is_lms_admin and quiz.course.instructor.user != request.user:
        raise PermissionDenied

    try:
        if request.POST.get('quick_points') is not None:
            points = float(request.POST.get('quick_points'))
        else:
            points = float(request.POST.get('points_earned', 0))
    except (TypeError, ValueError):
        points = 0.0
    points = max(0.0, min(points, float(answer.question.points)))

    answer.points_earned = points
    answer.is_correct = (points >= answer.question.points)
    answer.is_graded = True
    answer.graded_by = request.user
    answer.graded_at = timezone.now()
    answer.save()

    # Re-total the attempt's score now that this answer has real points,
    # and clear needs_grading once nothing is left waiting on review.
    attempt = answer.attempt
    total_points = quiz.total_points
    earned_points = attempt.answers.aggregate(total=models.Sum('points_earned'))['total'] or 0
    attempt.score = round((float(earned_points) / total_points) * 100, 2) if total_points else 0
    attempt.needs_grading = attempt.answers.filter(is_graded=False).exists()
    attempt.save(update_fields=['score', 'needs_grading'])

    messages.success(request, "Answer graded.")
    return redirect('quiz_grade_queue', pk=quiz.id)


@login_required
def quiz_delete(request, pk):
    if not has_quiz_permission(request.user):
        raise PermissionDenied
    quiz = _scoped_quiz_or_404(request, pk)

    if request.method == 'POST':
        title = quiz.title
        quiz.delete()
        messages.success(request, f"Deleted test «{title}».")
        return redirect('quiz_list')

    return render(request, 'quizzes/quiz_confirm_delete.html', {'quiz': quiz})


@login_required
def quiz_duplicate(request, pk):
    if not has_quiz_permission(request.user):
        raise PermissionDenied
    original = _scoped_quiz_or_404(request, pk)

    new_quiz = Quiz.objects.create(
        course=original.course,
        lesson=original.lesson,
        title=f"{original.title} (Copy)",
        description=original.description,
        created_by=request.user,
        status=Quiz.Status.DRAFT,
        time_limit_minutes=original.time_limit_minutes,
        max_attempts=original.max_attempts,
        passing_score=original.passing_score,
        shuffle_questions=original.shuffle_questions,
    )
    for q in original.questions.prefetch_related('choices').all():
        new_q = Question.objects.create(
            quiz=new_quiz, order=q.order, text=q.text, question_type=q.question_type,
            points=q.points, sample_answer=q.sample_answer,
        )
        Choice.objects.bulk_create([
            Choice(question=new_q, text=c.text, is_correct=c.is_correct, order=c.order)
            for c in q.choices.all()
        ])

    messages.success(request, f"Duplicated as «{new_quiz.title}» — it's a new draft, free to edit.")
    return redirect('quiz_builder_edit', pk=new_quiz.pk)


# ──────────────────────────────────────────────────────────
#  QUESTION BANK
#  Reusable, opt-in, course-scoped questions — deliberately not linked
#  back to any Quiz/Question. Saving copies data in; inserting into a
#  quiz copies data back out. No live link either direction.
# ──────────────────────────────────────────────────────────
def _bank_courses(user):
    """Courses a staff user is allowed to manage bank items for."""
    if user.is_lms_admin:
        return Course.objects.all().order_by('title')
    return Course.objects.filter(instructor__user=user).order_by('title')


@login_required
def question_bank_list(request):
    if not has_quiz_permission(request.user):
        raise PermissionDenied

    courses = _bank_courses(request.user)
    items = (
        QuestionBankItem.objects
        .filter(course__in=courses)
        .select_related('course')
        .prefetch_related('choices')
    )

    course_filter = request.GET.get('course', '')
    if course_filter:
        items = items.filter(course_id=course_filter)

    search_query = request.GET.get('search', '').strip()
    if search_query:
        items = items.filter(text__icontains=search_query)

    paginator = Paginator(items, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    for item in page_obj:
        item.lettered_choices = list(zip(string.ascii_uppercase, item.choices.all()))

    return render(request, 'quizzes/question_bank_list.html', {
        'items': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'courses': courses,
        'course_filter': course_filter,
        'search_query': search_query,
    })


@login_required
def question_bank_delete(request, pk):
    if not has_quiz_permission(request.user):
        raise PermissionDenied
    if request.method != 'POST':
        raise PermissionDenied

    item = get_object_or_404(QuestionBankItem, pk=pk, course__in=_bank_courses(request.user))
    item.delete()
    messages.success(request, "Removed from the question bank.")
    return redirect('question_bank_list')


@login_required
def question_bank_items(request):
    """AJAX: returns bank items for a course, shaped to drop straight into
    the builder's createQuestionCard(question) JS — same {text, type,
    points, sample_answer, choices} shape it already expects."""
    if not has_quiz_permission(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    course_id = request.GET.get('course')
    if not course_id:
        return JsonResponse({'items': []})

    course = _bank_courses(request.user).filter(pk=course_id).first()
    if not course:
        return JsonResponse({'items': []})

    items = QuestionBankItem.objects.filter(course=course).prefetch_related('choices').order_by('-created_at')

    data = [
        {
            'id': item.id,
            'text': item.text,
            'type': item.question_type,
            'points': item.points,
            'sample_answer': item.sample_answer,
            'choices': [{'text': c.text, 'is_correct': c.is_correct} for c in item.choices.all()],
        }
        for item in items
    ]
    return JsonResponse({'items': data})


@login_required
def question_bank_save(request):
    """AJAX: saves one question card from the builder into the bank as a
    standalone copy — no link back to whatever quiz it came from."""
    if not has_quiz_permission(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        payload = json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    course = _bank_courses(request.user).filter(pk=payload.get('course')).first()
    if not course:
        return JsonResponse({'error': 'Choose a valid course first.'}, status=400)

    text = (payload.get('text') or '').strip()
    if not text:
        return JsonResponse({'error': 'This question needs text before it can be saved.'}, status=400)

    q_type = payload.get('type') or Question.Type.SINGLE
    if q_type not in Question.Type.values:
        q_type = Question.Type.SINGLE

    try:
        points = int(payload.get('points') or 1)
    except (TypeError, ValueError):
        points = 1

    item = QuestionBankItem.objects.create(
        course=course,
        created_by=request.user,
        text=text,
        question_type=q_type,
        sample_answer=(payload.get('sample_answer') or '').strip(),
        points=max(points, 1),
    )
    for c_order, c in enumerate(payload.get('choices') or []):
        choice_text = (c.get('text') or '').strip()
        if not choice_text:
            continue
        QuestionBankChoice.objects.create(
            item=item, order=c_order, text=choice_text, is_correct=bool(c.get('is_correct')),
        )

    return JsonResponse({'status': 'ok', 'id': item.id})


# ──────────────────────────────────────────────────────────
#  GRADING HELPERS
# ──────────────────────────────────────────────────────────
def _grade_question(question, selected_ids):
    """
    Returns (points_earned, is_fully_correct) for one question's selections.

    SINGLE / TRUE_FALSE questions are all-or-nothing — there's only one
    right answer, so partial credit doesn't make sense.

    MULTIPLE (multi-select) questions use Moodle-style partial credit:
    each correct option picked earns 1/n of the question's points (n =
    number of correct options), each incorrect option picked costs 1/n,
    and the total is floored at 0 and capped at full marks. This rewards
    a student who got most of a multi-answer question right instead of
    scoring them the same as someone who got none of it.
    """
    correct_ids = question.correct_choice_ids
    points = question.points

    if question.question_type == Question.Type.MULTIPLE:
        if not correct_ids:
            return (0, False)
        num_correct = len(correct_ids)
        correct_picked = len(selected_ids & correct_ids)
        incorrect_picked = len(selected_ids - correct_ids)
        fraction = (correct_picked - incorrect_picked) / num_correct
        fraction = max(0.0, min(1.0, fraction))
        earned = round(fraction * points, 2)
        is_fully_correct = selected_ids == correct_ids
        return (earned, is_fully_correct)

    is_correct = bool(selected_ids) and selected_ids == correct_ids
    return ((points if is_correct else 0), is_correct)


def _grade_and_submit(attempt, answers_payload, auto=False):
    quiz = attempt.quiz
    total_points = 0
    earned_points = 0
    has_ungraded = False

    attempt.answers.all().delete()
    for question in quiz.questions.prefetch_related('choices').all():
        total_points += question.points
        raw = answers_payload.get(question.id)

        if question.question_type == Question.Type.SHORT_ANSWER:
            text = raw.strip() if isinstance(raw, str) else ''
            StudentAnswer.objects.create(
                attempt=attempt, question=question, text_answer=text,
                is_correct=False, points_earned=0,
                # A blank response has nothing to grade — treat it as
                # already graded (0 points) rather than sitting in the
                # queue forever. Only a real answer needs instructor review.
                is_graded=not bool(text),
            )
            if text:
                has_ungraded = True
            # Ungraded short answers don't contribute to earned_points yet —
            # the score stays provisional until an instructor grades them.
            continue

        selected_ids = set(raw or [])
        points_earned, is_fully_correct = _grade_question(question, selected_ids)

        answer = StudentAnswer.objects.create(
            attempt=attempt, question=question,
            is_correct=is_fully_correct, points_earned=points_earned, is_graded=True,
        )
        if selected_ids:
            answer.selected_choices.set(Choice.objects.filter(id__in=selected_ids, question=question))

        earned_points += points_earned

    attempt.score = round((earned_points / total_points) * 100, 2) if total_points else 0
    attempt.needs_grading = has_ungraded
    attempt.is_completed = True
    attempt.submitted_at = timezone.now()
    attempt.is_auto_submitted = auto
    attempt.save()
    return attempt


# ──────────────────────────────────────────────────────────
#  STUDENT: LIST / TAKE / RESULT
# ──────────────────────────────────────────────────────────
@login_required
def student_quiz_list(request):
    if request.user.role != 'STUDENT':
        return redirect('quiz_list')

    student = get_object_or_404(Student, user=request.user)
    view_mode = request.GET.get('view', 'history')

    if view_mode == 'available':
        # Enrolled courses
        enrolled_ids = set(Enrollment.objects.filter(student=student).values_list('course_id', flat=True))
        free_ids = set(Course.objects.filter(is_free=True).values_list('id', flat=True))
        accessible_ids = enrolled_ids | free_ids

        # Get quizzes in enrolled courses
        all_quizzes = Quiz.objects.filter(
            course_id__in=accessible_ids, status=Quiz.Status.PUBLISHED
        ).select_related('course').order_by('-created_at')

        available_quizzes = []
        for quiz in all_quizzes:
            attempts = QuizAttempt.objects.filter(quiz=quiz, student=student)
            completed_attempts = list(attempts.filter(is_completed=True).order_by('started_at'))
            completed_count = len(completed_attempts)
            in_progress = attempts.filter(is_completed=False).first()

            # Attach history metadata to the quiz object
            quiz.completed_attempts = completed_attempts
            quiz.attempts_count = completed_count
            quiz.attempts_remaining = max(quiz.max_attempts - completed_count, 0)
            
            # Find best score among completed attempts
            scores = [a.score for a in completed_attempts if a.score is not None]
            quiz.best_score = max(scores) if scores else None

            if in_progress:
                # Resume in-progress attempt
                quiz.in_progress_attempt = in_progress
                available_quizzes.append(quiz)
            elif completed_count < quiz.max_attempts and not quiz.is_past_due:
                # Still has retakes remaining and not expired
                available_quizzes.append(quiz)
            else:
                # Exhausted attempts or past due — show grayed out
                quiz.attempts_exhausted = True
                available_quizzes.append(quiz)

        # Get unique courses for available quizzes
        course_ids = all_quizzes.values_list('course_id', flat=True).distinct()
        courses = Course.objects.filter(id__in=course_ids)

        # Sized generously — the page already has instant client-side
        # search/filter (testSearchInput, courseSelectFilter, status
        # pills) across whatever's loaded, so a small page size would
        # make that filter feel broken past page 1. This just caps the
        # worst case instead of loading an unbounded list.
        paginator = Paginator(available_quizzes, 30)
        page_obj = paginator.get_page(request.GET.get('page'))

        return render(request, 'quizzes/student_quiz_list.html', {
            'quizzes': page_obj,
            'page_obj': page_obj,
            'is_paginated': page_obj.has_other_pages(),
            'courses': courses,
            'view_mode': 'available',
        })
    else:
        status_filter = request.GET.get('status', 'all')
        attempts = QuizAttempt.objects.filter(student=student).select_related('quiz__course').order_by('-started_at')

        # Get unique courses that have attempts
        course_ids = attempts.values_list('quiz__course_id', flat=True).distinct()
        courses = Course.objects.filter(id__in=course_ids)

        if status_filter == 'completed':
            attempts = attempts.filter(is_completed=True)
        elif status_filter == 'in_progress':
            attempts = attempts.filter(is_completed=False)

        paginator = Paginator(attempts, 30)
        page_obj = paginator.get_page(request.GET.get('page'))

        return render(request, 'quizzes/student_quiz_list.html', {
            'attempts': page_obj,
            'page_obj': page_obj,
            'is_paginated': page_obj.has_other_pages(),
            'courses': courses,
            'status_filter': status_filter,
            'view_mode': 'history',
        })


@login_required
def quiz_take(request, pk):
    if request.user.role != 'STUDENT':
        raise PermissionDenied

    quiz = get_object_or_404(
        Quiz.objects.prefetch_related('questions__choices'), pk=pk, status=Quiz.Status.PUBLISHED
    )
    student = get_object_or_404(Student, user=request.user)

    is_enrolled = Enrollment.objects.filter(student=student, course=quiz.course).exists()
    if not (is_enrolled or quiz.course.is_free):
        raise PermissionDenied

    existing = QuizAttempt.objects.filter(quiz=quiz, student=student)
    attempt = existing.filter(is_completed=False).first()

    if not attempt:
        if quiz.is_past_due:
            messages.error(request, "This test's due date has passed.")
            return redirect('student_quiz_list')
        if existing.filter(is_completed=True).count() >= quiz.max_attempts:
            messages.error(request, "You've used all your attempts for this test.")
            return redirect('student_quiz_list')
        attempt = QuizAttempt.objects.create(quiz=quiz, student=student)

    if request.method == 'POST':
        # A real submission always wins, even if it lands right as the
        # deadline ticks over — the client-side timer already triggers its
        # own auto-submit at zero, so a POST arriving here reflects genuine
        # answers and shouldn't be discarded by a server-clock race.
        answers_payload = {}
        for question in quiz.questions.all():
            if question.question_type == Question.Type.SHORT_ANSWER:
                answers_payload[question.id] = request.POST.get(f'question_{question.id}', '')
            else:
                selected = request.POST.getlist(f'question_{question.id}')
                answers_payload[question.id] = [int(v) for v in selected if v.isdigit()]
        auto = request.POST.get('auto_submit') == '1'
        _grade_and_submit(attempt, answers_payload, auto=auto)
        return redirect('quiz_result', pk=attempt.pk)

    # GET: if the timer already ran out before they came back (browser
    # closed, tab crashed...), grade whatever was autosaved rather than
    # wiping every answer blank.
    if attempt.deadline and timezone.now() > attempt.deadline:
        saved_answers = {}
        for ans in attempt.answers.prefetch_related('selected_choices').select_related('question').all():
            if ans.question.question_type == Question.Type.SHORT_ANSWER:
                saved_answers[ans.question_id] = ans.text_answer
            else:
                saved_answers[ans.question_id] = list(ans.selected_choices.values_list('id', flat=True))
        _grade_and_submit(attempt, saved_answers, auto=True)
        return redirect('quiz_result', pk=attempt.pk)

    questions = list(quiz.questions.all())
    if quiz.shuffle_questions:
        random.shuffle(questions)

    for question in questions:
        choices = list(question.choices.all())
        if quiz.shuffle_questions:
            # Seeded on attempt + question so the order is stable across
            # page reloads/autosaves within this attempt, but still
            # different per student and per attempt.
            random.Random(f"{attempt.id}-{question.id}").shuffle(choices)
        question.display_choices = choices

    # Hydrate the form with anything already autosaved for this attempt.
    saved_choice_ids = {
        ans.question_id: set(ans.selected_choices.values_list('id', flat=True))
        for ans in attempt.answers.prefetch_related('selected_choices').all()
    }
    saved_text = {
        ans.question_id: ans.text_answer
        for ans in attempt.answers.all()
    }
    for question in questions:
        question.selected_choice_ids = saved_choice_ids.get(question.id, set())
        question.saved_text = saved_text.get(question.id, '')

    return render(request, 'quizzes/quiz_take.html', {
        'quiz': quiz, 'attempt': attempt, 'questions': questions,
        'has_multi_select': any(q.question_type == Question.Type.MULTIPLE for q in questions),
    })


@login_required
def quiz_autosave(request, pk):
    """
    Periodically called from the test-taking page so a browser crash or
    accidental tab close doesn't lose a student's in-progress answers.
    Stores selections as-is without grading — grading only ever happens
    on final submit via _grade_and_submit.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    if request.user.role != 'STUDENT':
        return JsonResponse({'error': 'Forbidden'}, status=403)

    attempt = get_object_or_404(QuizAttempt, pk=pk, student__user=request.user)
    if attempt.is_completed:
        return JsonResponse({'error': 'This attempt was already submitted.'}, status=400)
    if attempt.deadline and timezone.now() > attempt.deadline:
        return JsonResponse({'error': 'Time is up for this attempt.'}, status=400)

    try:
        payload = json.loads(request.body)
        answers = payload.get('answers', {})
        if not isinstance(answers, dict):
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    valid_questions = {q.id: q for q in attempt.quiz.questions.all()}

    for q_id_str, value in answers.items():
        try:
            question_id = int(q_id_str)
        except (TypeError, ValueError):
            continue
        question = valid_questions.get(question_id)
        if not question:
            continue

        answer, _ = StudentAnswer.objects.get_or_create(attempt=attempt, question_id=question_id)

        if question.question_type == Question.Type.SHORT_ANSWER:
            if isinstance(value, str):
                answer.text_answer = value[:10000]  # sane upper bound
                answer.save(update_fields=['text_answer'])
        elif isinstance(value, list):
            # Only accept choice IDs that actually belong to this question —
            # closes off a crafted payload trying to mark other questions' choices.
            valid_choices = Choice.objects.filter(question_id=question_id, id__in=value)
            answer.selected_choices.set(valid_choices)

    return JsonResponse({'status': 'saved', 'saved_at': timezone.now().isoformat()})


@login_required
def quiz_result(request, pk):
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related('quiz__course', 'student__user'), pk=pk
    )
    user = request.user

    if user.role == 'STUDENT':
        if attempt.student.user != user:
            raise PermissionDenied
    elif has_quiz_permission(user):
        if not user.is_lms_admin and attempt.quiz.course.instructor.user != user:
            raise PermissionDenied
    else:
        raise PermissionDenied

    if not attempt.is_completed:
        if user.role == 'STUDENT':
            return redirect('quiz_take', pk=attempt.quiz.id)
        messages.info(request, "This attempt is still in progress.")
        return redirect('quiz_detail', pk=attempt.quiz.id)

    answers = attempt.answers.select_related('question').prefetch_related(
        'selected_choices', 'question__choices'
    )

    # Sum earned points across all answers for the current attempt.
    points_earned = answers.aggregate(total=models.Sum('points_earned'))['total'] or 0

    # All completed attempts for this student on this quiz (for history panel).
    past_attempts = (
        QuizAttempt.objects
        .filter(quiz=attempt.quiz, student=attempt.student, is_completed=True)
        .order_by('-submitted_at')
    )
    attempts_used = past_attempts.count()
    attempts_remaining = max(attempt.quiz.max_attempts - attempts_used, 0)

    return render(request, 'quizzes/quiz_result.html', {
        'attempt': attempt,
        'answers': answers,
        'points_earned': points_earned,
        'past_attempts': past_attempts,
        'attempts_remaining': attempts_remaining,
    })
