from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'course', 'student', 'rating', 'is_approved']
    list_filter = ['rating', 'is_approved', 'course']
    search_fields = ['student__user__username', 'course__title', 'comment']
    list_editable = ['is_approved'] 
