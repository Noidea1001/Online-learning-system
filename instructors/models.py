# instructors/models.py
from django.conf import settings
from django.db import models

class Instructor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='instructor_profile'
    )
    specialty = models.CharField(max_length=100, default="Expert Mentor")
    experience_years = models.PositiveIntegerField(default=1)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.specialty}"
