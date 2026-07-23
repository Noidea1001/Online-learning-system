# assignments/models.py
from django.db import models

class Assignment(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='assignments')
    lesson = models.ForeignKey('lessons.Lesson', on_delete=models.CASCADE, related_name='assignments', null=True, blank=True)    
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField()
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    assignment_file = models.FileField(
        upload_to='assignments/files/', 
        null=True, 
        blank=True, 
        help_text="Upload instruction document, template files, or project resources (PDF, ZIP, DOCX)."
    )

    class Meta:
        ordering = ['id'] 

    def __str__(self):
        return self.title
