from django.db import models

class Submission(models.Model):
    assignment = models.ForeignKey('assignments.Assignment', on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='submissions')
    submitted_file = models.FileField(upload_to='submissions/', blank=True, null=True)
    text_content = models.TextField(blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('assignment', 'student')
        
    def __str__(self):
        return f"Submission by {self.student.user.username} for {self.assignment.title}"
