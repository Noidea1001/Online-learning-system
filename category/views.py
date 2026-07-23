# category/views.py
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from .models import Category
from .forms import CategoryForm
from django.shortcuts import render, redirect, get_object_or_404


def _is_management_allowed(user):
    # can access if user is superuser or has role EMPLOYEE
    return user.is_superuser or getattr(user, 'role', None) == 'EMPLOYEE'


@login_required
def category_list(request):
    # can access if user is superuser or has role EMPLOYEE or INSTRUCTOR
    if not request.user.is_superuser and getattr(request.user, 'role', None) not in ['EMPLOYEE', 'INSTRUCTOR']:
        raise PermissionDenied
    return render(request, 'category/category_list.html', {'categories': Category.objects.all()})


@login_required
def category_detail(request, pk):
    # can access if user is superuser or has role EMPLOYEE or INSTRUCTOR
    if not request.user.is_superuser and getattr(request.user, 'role', None) not in ['EMPLOYEE', 'INSTRUCTOR']:
        raise PermissionDenied
    category = get_object_or_404(Category, pk=pk)
    
    if getattr(request.user, 'role', None) == 'INSTRUCTOR':
        courses = category.courses.filter(instructor=getattr(request.user, 'instructor_profile', None))
    else:
        courses = category.courses.all()
        
    return render(request, 'category/category_detail.html', {'category': category, 'courses': courses})


@login_required
def category_create(request):
    if not _is_management_allowed(request.user):
        raise PermissionDenied
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category created successfully.")
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'category/category_form.html', {'form': form, 'action': 'Add'})


@login_required
def category_update(request, pk):
    if not _is_management_allowed(request.user):
        raise PermissionDenied
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f"Category '{category.name}' updated successfully.")
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'category/category_form.html', {'form': form, 'category': category, 'action': 'Edit'})


@login_required
def category_delete(request, pk):
    if not _is_management_allowed(request.user):
        raise PermissionDenied
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f"Category '{name}' deleted successfully.")
        return redirect('category_list')
    return render(request, 'category/category_confirm_delete.html', {'category': category})
