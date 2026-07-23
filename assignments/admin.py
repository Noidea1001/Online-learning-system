from django.contrib import admin
from .models import Assignment

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'lesson', 'due_date', 'max_score']
    list_filter = ['lesson__course', 'due_date']
    search_fields = ['title', 'description']
