from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'date_of_birth', 'enrolled_date']
    search_fields = ['user__username', 'user__email']
