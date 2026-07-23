# enrollments/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils import timezone
from courses.models import Course
from students.models import Student
from .models import Enrollment
from .forms import EnrollmentForm

@login_required
def enrollment_list(request):
    user = request.user
    user_role = str(getattr(user, 'role', '')).strip()
    
    if not user.is_superuser and user_role not in ['EMPLOYEE', 'INSTRUCTOR']:
        raise PermissionDenied
        
    all_students = Student.objects.all().select_related('user')
    all_courses = Course.objects.all()
    
    if user.is_superuser or user_role == 'EMPLOYEE':
        enrollments = Enrollment.objects.all().select_related('student__user', 'course')
    elif user_role == 'INSTRUCTOR':
        instructor_profile = getattr(user, 'instructor_profile', None)
        enrollments = Enrollment.objects.filter(
            course__instructor=instructor_profile
        ).select_related('student__user', 'course').order_by('-enrolled_at')
    
    context = {
        'enrollments': enrollments,
        'all_students': all_students,
        'all_courses': all_courses,
    }
    return render(request, 'enrollments/enrollment_list.html', context)


@login_required
def enrollment_create(request):
    user_role = str(getattr(request.user, 'role', '')).strip()
    if not request.user.is_superuser and user_role != 'EMPLOYEE':
        raise PermissionDenied

    if request.method == 'POST':
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            enrollment = form.save()
            messages.success(request, f"Successfully enrolled student into '{enrollment.course.title}'!")
            return redirect('enrollment_list')
        else:
            messages.error(request, "Enrollment failed. Please verify the input values.")
    else:
        form = EnrollmentForm()

    return render(request, 'enrollments/enrollment_form.html', {'form': form})


@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    student = None
    user = request.user
    user_role = str(getattr(user, 'role', '')).strip()
    
    # Case 1: Triggered by an Administrative LMS Operative
    if user.is_superuser or user_role == 'EMPLOYEE':
        student_id = request.POST.get('student_id') or request.GET.get('student_id')
        if student_id:
            student = get_object_or_404(Student, id=student_id)
        else:
            student = getattr(user, 'student_profile', None)
            if not student:
                messages.error(request, "Please select a student to enroll in this course.")
                return redirect('course_detail', pk=course.id)
                
    # Case 2: Triggered directly by an active Student consumer profile
    else:
        if user_role == 'STUDENT':
            try:
                student = Student.objects.get(user=user)
            except Student.DoesNotExist:
                messages.error(request, "Your student profile is incomplete. Please contact support.")
                return redirect('course_detail', pk=course.id)
        else:
            raise PermissionDenied

    if not student:
        messages.error(request, "Failed to process enrollment because student account was not found.")
        return redirect('course_detail', pk=course.id)

    # Establish record transaction loop safely avoiding duplicates
    enrollment, created = Enrollment.objects.get_or_create(student=student, course=course)
    
    if created:
        # Automatically mark free open access tracks as Paid instantly
        if getattr(course, 'is_free', False) or (course.price and course.price <= 0):
            enrollment.is_paid = True
            enrollment.save()
            messages.success(request, f"Successfully enrolled in '{course.title}'. Enjoy learning!")
        else:
            # Re-route premium access modules directly to checkout window ledgers
            messages.info(request, f"Enrolled in '{course.title}'. Please complete your payment to unlock the content.")
            return redirect('pay_course', course_id=course.id)
    else:
        messages.warning(request, f"You are already enrolled in this course.")

    if user.is_superuser or user_role == 'EMPLOYEE':
        return redirect('enrollment_list')
    return redirect('course_detail', pk=course.id)


@login_required
def enrollment_detail(request, pk):
    user = request.user
    user_role = str(getattr(user, 'role', '')).strip()
    enrollment = get_object_or_404(Enrollment.objects.select_related('student__user', 'course'), pk=pk)
    
    is_authorized = user.is_superuser or user_role == 'EMPLOYEE'
    if not is_authorized and user_role == 'INSTRUCTOR':
        is_authorized = (enrollment.course.instructor == getattr(user, 'instructor_profile', None))
        
    if not is_authorized:
        raise PermissionDenied
        
    return render(request, 'enrollments/enrollment_detail.html', {'enrollment': enrollment})


@login_required
def enrollment_update(request, pk):
    user_role = str(getattr(request.user, 'role', '')).strip()
    if not request.user.is_superuser and user_role != 'EMPLOYEE':
        raise PermissionDenied
    enrollment = get_object_or_404(Enrollment, pk=pk)
    
    if request.method == 'POST':
        form = EnrollmentForm(request.POST, instance=enrollment)
        if form.is_valid():
            form.save()
            return redirect('enrollment_list')
    else:
        form = EnrollmentForm(instance=enrollment)
        
    return render(request, 'enrollments/enrollment_form.html', {'form': form, 'enrollment': enrollment})


@login_required
def enrollment_delete(request, pk):
    user_role = str(getattr(request.user, 'role', '')).strip()
    if not request.user.is_superuser and user_role != 'EMPLOYEE':
        raise PermissionDenied
        
    enrollment = get_object_or_404(Enrollment, pk=pk)
    if request.method == 'POST':
        student_name = enrollment.student.user.username
        course_title = enrollment.course.title
        enrollment.delete()
        messages.success(request, f"Successfully deleted student {student_name} from course {course_title}.")
        return redirect('enrollment_list')
        
    return render(request, 'enrollments/enrollment_confirm_delete.html', {'enrollment': enrollment})


@login_required
def pay_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user_role = str(getattr(request.user, 'role', '')).strip()
    if user_role != 'STUDENT' or not hasattr(request.user, 'student_profile'):
        raise PermissionDenied
        
    enrollment = get_object_or_404(Enrollment, student=request.user.student_profile, course=course)

    if enrollment.is_paid:
        messages.info(request, "This course has already been paid for.")
        return redirect('course_detail', pk=course.id)
        
    if request.method == 'POST':
        enrollment.is_paid = True
        enrollment.save()
        messages.success(request, f"Payment {course.title} successfully.")
        return redirect('course_detail', pk=course.id)
        
    return render(request, 'enrollments/payment_checkout.html', {
        'course': course,
        'enrollment': enrollment,
    })


@login_required
def toggle_payment_status(request, pk):
  
    user = request.user
    user_role = str(getattr(user, 'role', '')).strip() # 🎯 ជួសជុល៖ សម្អាតដកឃ្លាជ្រុល
    
    if not user.is_superuser and user_role != 'EMPLOYEE':
        raise PermissionDenied
        
    enrollment = get_object_or_404(Enrollment, pk=pk)
    
    if request.method == 'POST':
        enrollment.is_paid = not enrollment.is_paid
        enrollment.save()
        
        student_name = enrollment.student.user.get_full_name() or enrollment.student.user.username
        if enrollment.is_paid:
            messages.success(request, f"Payment verified for {student_name} (Paid).")
        else:
            messages.info(request, f"Payment status reverted to Unpaid for {student_name}.")
            
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('enrollment_list')
