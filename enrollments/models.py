from courses.models import Course
from django.db import models

class Enrollment(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False, help_text="Designates whether the course fee has been paid.")
    completed_lessons = models.ManyToManyField('lessons.Lesson', blank=True, related_name='completed_by')

    class Meta:
        unique_together = ('student', 'course')

    @property
    def progress_percent(self):
        total = self.course.lessons.count()
        if total == 0:
            return 0
        completed = self.completed_lessons.count()
        return int((completed / total) * 100)

    def __str__(self):
        return f"{self.student.user.username} enrolled in {self.course.title}"
