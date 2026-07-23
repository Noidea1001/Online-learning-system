from django.contrib import admin
from .models import Submission

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'assignment', 'student', 'score', 'submitted_at']
    list_filter = ['score', 'submitted_at']
    search_fields = ['student__user__username', 'assignment__title']
