# employees/admin.py
from django.contrib import admin
from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'get_username',
        'get_full_name',
        'job_title',
        'department',
        'status',
        'hire_date',
        'salary_display',
    ]
    
    list_filter = ['status', 'department', 'hire_date']
    
    search_fields = [
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'job_title',
        'department',
    ]
    
    raw_id_fields = ['user']
    ordering = ['-hire_date', 'user__username']
    
    fieldsets = [
        ('Account Information', {
            'fields': ['user', 'status']
        }),
        ('Job Information', {
            'fields': ['job_title', 'department', 'hire_date', 'salary']
        }),
    ]

    def get_username(self, obj):
        return obj.user.username if obj.user else '-'
    get_username.short_description = 'Username'
    get_username.admin_order_field = 'user__username'

    def get_full_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return '-'
    get_full_name.short_description = 'Full Name'

    def salary_display(self, obj):
        if obj.salary:
            return f"${obj.salary:,.2f}"
        return '-'
    salary_display.short_description = 'Salary'

    # Custom Actions
    actions = ['mark_as_active', 'mark_as_inactive']

    def mark_as_active(self, request, queryset):
        queryset.update(status='active')
    mark_as_active.short_description = "Change to Active"

    def mark_as_inactive(self, request, queryset):
        queryset.update(status='inactive')
    mark_as_inactive.short_description = "Change to Inactive"