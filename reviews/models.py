# reviews/models.py
from django.db import models

class Review(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField() 
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        unique_together = ('course', 'student')
