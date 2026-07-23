# employees/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash  
from django.db.models import Q
from django.db import transaction

from .models import Employee
from .forms import EmployeeForm 

User = get_user_model()


@login_required
def employee_dashboard(request):
    if not request.user.is_superuser and getattr(request.user, 'role', None) != 'EMPLOYEE':
        raise PermissionDenied
        
    return redirect('dashboard_home')


@login_required
def employee_list(request): 
    if not request.user.is_superuser and getattr(request.user, 'role', None) != 'EMPLOYEE':
        raise PermissionDenied
        
    queryset = Employee.objects.all().select_related('user')

    search_query = request.GET.get('search', '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(job_title__icontains=search_query)
        )

    department_filter = request.GET.get('department', '').strip()
    if department_filter:
        queryset = queryset.filter(department=department_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        if status_filter == 'active':
            queryset = queryset.filter(user__is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(user__is_active=False)

    departments = Employee.objects.exclude(department__isnull=True).exclude(department='').values_list('department', flat=True).distinct()

    context = {
        'employees': queryset,
        'departments': departments,
    }
    return render(request, 'employees/employee_list.html', context)


@login_required
def employee_detail(request, pk): 
    employee = get_object_or_404(Employee.objects.select_related('user'), pk=pk)
    
    user_role = getattr(request.user, 'role', None)
    if not request.user.is_superuser and user_role != 'EMPLOYEE' and employee.user != request.user:
        raise PermissionDenied
        
    return render(request, 'employees/employee_detail.html', {'employee': employee})


@login_required
def employee_create(request):
    if not request.user.is_superuser:
        raise PermissionDenied
        
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                messages.success(request, "Create Employee Successful.")
                return redirect('employee_list')
            except Exception as e:
                messages.error(request, "An unexpected database error occurred. Please try again.")
        else:
            messages.error(request, "Failed to create employee account. Please resolve the errors below.")
    else:
        form = EmployeeForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'employee': None, 'title': 'Create Employee'})


@login_required
def employee_update(request, pk): 
    employee = get_object_or_404(Employee.objects.select_related('user'), pk=pk)
    
    if not request.user.is_superuser and employee.user != request.user:
        raise PermissionDenied
        
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            try:
                with transaction.atomic():
                    updated_employee = form.save()
                
                updated_user = updated_employee.user
                
                if request.user == updated_user:
                    update_session_auth_hash(request, updated_user)
                    
                messages.success(request, f"Update Employee {updated_user.username} Successful.")
                
                if request.user.is_superuser:
                    return redirect('employee_list')
                return redirect('employee_detail', pk=employee.id)
            except Exception as e:
                messages.error(request, "An error occurred while updating the profile.")
        else:
            messages.error(request, "Failed to update profile. Please verify your input data.")
    else:
        try:
            form = EmployeeForm(instance=employee)
        except Exception:
            employee.image = None
            form = EmployeeForm(instance=employee)
            
    return render(request, 'employees/employee_form.html', {'form': form, 'employee': employee, 'title': 'Update Employee Information'})


@login_required
def employee_delete(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied
        
    employee = get_object_or_404(Employee.objects.select_related('user'), pk=pk)
    if request.method == 'POST':
        username = employee.user.username
        
        try:
            employee.user.delete()
        except Exception:
            employee.image = None
            employee.user.delete()
            
        messages.success(request, f"Delete Employee {username} Successful.")
        return redirect('employee_list')
        
    return render(request, 'employees/employee_confirm_delete.html', {'employee': employee})
