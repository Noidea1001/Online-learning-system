# reviews/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied 
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from django.db.models import Q  
from django.contrib import messages 
from .models import Review
from courses.models import Course
from enrollments.models import Enrollment 
from .forms import ReviewForm  


@login_required
def review_list(request):
    user = request.user
    
    if not user.is_superuser and user.role not in ['EMPLOYEE', 'INSTRUCTOR']:
        raise PermissionDenied
        
    if user.is_superuser or user.role == 'EMPLOYEE':
        reviews = Review.objects.all().select_related('student__user', 'course__instructor__user').order_by('-id')
        pending_count = Review.objects.filter(is_approved=False).count()
        
    elif user.role == 'INSTRUCTOR':
        instructor_profile = getattr(user, 'instructor_profile', None)
        reviews = Review.objects.filter(course__instructor=instructor_profile).select_related('student__user', 'course__instructor__user').order_by('-id')
        pending_count = Review.objects.filter(course__instructor=instructor_profile, is_approved=False).count()

    # use for search
    query = request.GET.get('search', '').strip()
    if query:
        reviews = reviews.filter(
            Q(student__user__username__icontains=query) |
            Q(student__user__first_name__icontains=query) |
            Q(student__user__last_name__icontains=query) |
            Q(course__title__icontains=query) |
            Q(comment__icontains=query)
        )
        
    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'pending':
        reviews = reviews.filter(is_approved=False)
    elif status_filter == 'approved':
        reviews = reviews.filter(is_approved=True)
    
    return render(request, 'reviews/review_list.html', {
        'reviews': reviews,
        'pending_count': pending_count
    })


@login_required
def review_create(request, course_id):
    if request.user.role != 'STUDENT' or not hasattr(request.user, 'student_profile'):
        raise PermissionDenied
        
    course = get_object_or_404(Course, id=course_id)
    student_profile = request.user.student_profile

    has_enrolled = Enrollment.objects.filter(student=student_profile, course=course).exists()
    if not has_enrolled and not request.user.is_superuser:
        messages.error(request, "You must be enrolled in this course to leave a review.")
        return redirect('course_detail', pk=course.id)

    already_reviewed = Review.objects.filter(course=course, student=student_profile).exists()
    if already_reviewed:
        messages.warning(request, "You have already submitted a review for this course.")
        return redirect('course_detail', pk=course.id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.course = course
            review.student = student_profile
            review.save()
            messages.success(request, "Thank you! Your review has been submitted for approval.")
            return redirect('course_detail', pk=course.id)
    else:
        form = ReviewForm()
        
    return render(request, 'reviews/review_form.html', {'form': form, 'course': course})


@login_required
def review_approve(request, pk):
    if not request.user.is_superuser and request.user.role != 'EMPLOYEE':
        raise PermissionDenied
        
    review = get_object_or_404(Review, pk=pk)
    
    if request.method == 'POST':
        review.is_approved = not review.is_approved
        review.save()
        if review.is_approved:
            messages.success(request, f"Review by @{review.student.user.username} approved live!")
        else:
            messages.info(request, f"Review by @{review.student.user.username} unapproved.")
            
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('review_list')


@method_decorator(login_required, name='dispatch')
class ReviewDetailView(DetailView):
    model = Review
    template_name = 'reviews/review_detail.html'
    context_object_name = 'review'

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        
        if not user.is_superuser and user.role not in ['EMPLOYEE', 'INSTRUCTOR']:
            raise PermissionDenied
            
        review = self.get_object()
        
        if user.role == 'INSTRUCTOR':
            instructor_profile = getattr(user, 'instructor_profile', None)
            if review.course.instructor != instructor_profile:
                raise PermissionDenied 
                
        return super().dispatch(request, *args, **kwargs)


@login_required
def review_delete(request, pk):
    if not request.user.is_superuser and request.user.role != 'EMPLOYEE':
        raise PermissionDenied
    review = get_object_or_404(Review, pk=pk)
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, "Review deleted successfully.")
        return redirect('review_list')
        
    return render(request, 'reviews/review_confirm_delete.html', {
        'review': review,
        'object': review
    })
