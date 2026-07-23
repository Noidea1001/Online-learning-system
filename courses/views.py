# courses/views.py
import fractions
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView
from django.db.models import Q, Max
from .models import Course, Tag
from .forms import CourseForm, TagForm
from category.models import Category
from instructors.models import Instructor
from students.models import Student
from assignments.models import Assignment 

class CourseListView(ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'

    def get_queryset(self):
        user = self.request.user
        
        if user.is_authenticated and (user.is_superuser or user.role == 'EMPLOYEE'):
            queryset = Course.objects.all()
        elif user.is_authenticated and user.role == 'INSTRUCTOR':
            instructor_profile = getattr(user, 'instructor_profile', None)
            queryset = Course.objects.filter(instructor=instructor_profile)
        else:
            queryset = Course.objects.filter(is_published=True)

        # Text Search Queries
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(instructor__user__first_name__icontains=search_query) | 
                Q(instructor__user__last_name__icontains=search_query) |
                Q(instructor__user__username__icontains=search_query)
            )

        # Handle Toolbar Selector Filters
        category_id = self.request.GET.get('category', '')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        instructor_id = self.request.GET.get('instructor', '')
        if instructor_id:
            queryset = queryset.filter(instructor_id=instructor_id)

        tag_id = self.request.GET.get('tag', '')
        if tag_id:
            queryset = queryset.filter(tags__id=tag_id)

        return queryset.select_related('category', 'instructor__user').prefetch_related('tags').distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['instructors'] = Instructor.objects.all().select_related('user')
        context['tags'] = Tag.objects.all()
        
        context['total_published'] = Course.objects.filter(is_published=True).count()
        return context

    # AJAX Live Search Interceptor Method Block
    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            self.template_name = 'courses/course_grid_partial.html'
        return super().render_to_response(context, **response_kwargs)

class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    login_url = 'login'
    redirect_field_name = 'next'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        user = self.request.user

        try:
            _is_free = bool(course.is_free)
        except Exception:
            _is_free = course.price <= 0

        is_enrolled = False
        enrollment_obj = None
        if user.is_authenticated:
            if user.is_superuser or getattr(user, 'role', None) == 'EMPLOYEE':
                is_enrolled = True
            elif getattr(user, 'role', None) == 'INSTRUCTOR' and course.instructor == getattr(user, 'instructor_profile', None):
                is_enrolled = True
            elif hasattr(user, 'student_profile'):
                try:
                    from enrollments.models import Enrollment
                    enrollment_obj = Enrollment.objects.filter(student=user.student_profile, course=course).first()
                    if enrollment_obj:
                        if _is_free or enrollment_obj.is_paid:
                            is_enrolled = True
                except Exception:
                    pass

        context['is_enrolled'] = is_enrolled
        context['enrollment'] = enrollment_obj
        context['course_is_free'] = _is_free
        context['all_students'] = None
        context['user_instructor'] = getattr(user, 'instructor_profile', None)

        if user.is_authenticated and (user.is_superuser or user.role == 'EMPLOYEE' or getattr(user, 'role', None) == 'INSTRUCTOR'):
            context['all_students'] = Student.objects.all().select_related('user')

        context['course_wide_assignments'] = Assignment.objects.filter(
            course=course,
            lesson__isnull=True
        )

        published_quizzes = list(course.quizzes.filter(status='PUBLISHED').order_by('-created_at'))
        context['published_quizzes'] = published_quizzes

        if user.is_authenticated and hasattr(user, 'student_profile'):
            from quizzes.models import QuizAttempt
            student = user.student_profile
            for quiz in published_quizzes:
                attempts = QuizAttempt.objects.filter(quiz=quiz, student=student)
                completed = attempts.filter(is_completed=True)
                in_progress = attempts.filter(is_completed=False).first()
                quiz.progress = {
                    'attempts_used': completed.count(),
                    'attempts_remaining': max(quiz.max_attempts - completed.count(), 0),
                    'best_score': completed.aggregate(best=Max('score'))['best'],
                    'in_progress_id': in_progress.id if in_progress else None,
                    'can_attempt': (completed.count() < quiz.max_attempts) and not quiz.is_past_due,
                }

        return context


# ==================== FUNCTION VIEWS ====================

@login_required
def course_create(request):
    if not request.user.is_superuser and request.user.role not in ['EMPLOYEE', 'INSTRUCTOR']:
        raise PermissionDenied
        
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            course = form.save(commit=False)
            if getattr(request.user, 'role', None) == 'INSTRUCTOR':
                course.instructor = getattr(request.user, 'instructor_profile', None)
            else:
                course.instructor = form.cleaned_data.get('instructor')
            course.save()
            form.save_m2m()
            messages.success(request, "Course has been created successfully.")
            return redirect('course_list')
    else:
        form = CourseForm(user=request.user)
    return render(request, 'courses/course_form.html', {'form': form, 'action': 'Add'})


@login_required
def course_update(request, pk):
    course = get_object_or_404(Course, pk=pk)
    
    if not request.user.is_superuser and request.user.role != 'EMPLOYEE':
        if course.instructor != getattr(request.user, 'instructor_profile', None):
            raise PermissionDenied
        
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course, user=request.user)
        if form.is_valid():
            course = form.save(commit=False)
            
            if form.cleaned_data.get('instructor'):
                course.instructor = form.cleaned_data.get('instructor')
            else:
                if request.user.role == 'INSTRUCTOR':
                    course.instructor = getattr(request.user, 'instructor_profile', None)
                    
            course.save()
            form.save_m2m()
            messages.success(request, f"Course {course.title} has been updated successfully.")
            return redirect('course_list')
    else:
        try:
            form = CourseForm(instance=course, user=request.user)
        except Exception:
            course.image = None
            form = CourseForm(instance=course, user=request.user)
            
    return render(request, 'courses/course_form.html', {'form': form, 'course': course, 'action': 'Edit'})


@login_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if not request.user.is_superuser and request.user.role != 'EMPLOYEE':
        if request.user.role == 'INSTRUCTOR':
            instructor_profile = getattr(request.user, 'instructor_profile', None)
            if course.instructor != instructor_profile:
                raise PermissionDenied
        else:
            raise PermissionDenied

    if request.method == 'POST':
        course_title = course.title
        try:
            course.delete()
        except Exception:
            course.image = None
            course.delete()
        messages.success(request, f"Course «{course_title}» has been deleted successfully.")
        return redirect('course_list')
        
    return render(request, 'courses/course_confirm_delete.html', {'course': course})


@login_required
def tag_list(request):
    if not request.user.is_superuser and request.user.role not in ['EMPLOYEE', 'INSTRUCTOR']:
        raise PermissionDenied
    return render(request, 'courses/tag_list.html', {'tags': Tag.objects.all()})


@login_required
def tag_create(request):
    if not request.user.is_superuser and request.user.role not in ['EMPLOYEE', 'INSTRUCTOR']:
        raise PermissionDenied
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tag has been created successfully.")
            return redirect('tag_list')
    else:
        form = TagForm()
    return render(request, 'courses/tag_form.html', {'form': form, 'action': 'Add'})


@login_required
def tag_update(request, pk):
    if not request.user.is_superuser and request.user.role not in ['EMPLOYEE', 'INSTRUCTOR']:
        raise PermissionDenied
        
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, f"Tag «{tag.name}» has been updated successfully.")
            return redirect('tag_list')
    else:
        form = TagForm(instance=tag)
    return render(request, 'courses/tag_form.html', {'form': form, 'tag': tag, 'action': 'Edit'})


@login_required
def tag_delete(request, pk):
    if not request.user.is_superuser and request.user.role not in ['EMPLOYEE', 'INSTRUCTOR']:
        raise PermissionDenied
        
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == 'POST':
        tag_name = tag.name
        tag.delete()
        messages.success(request, f"Tag «{tag_name}» has been deleted successfully.")
        return redirect('tag_list')
    return render(request, 'courses/tag_confirm_delete.html', {'tag': tag})
