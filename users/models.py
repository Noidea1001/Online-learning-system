from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        INSTRUCTOR = 'INSTRUCTOR', 'Instructor'
        EMPLOYEE = 'EMPLOYEE', 'Employee'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT
    )

    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='users/profiles/', blank=True, null=True)

    @property
    def avatar_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        if self.role == 'STUDENT' and hasattr(self, 'student_profile') and self.student_profile.profile_picture:
            return self.student_profile.profile_picture.url
        if self.role == 'EMPLOYEE' and hasattr(self, 'employee_profile') and self.employee_profile.image:
            return self.employee_profile.image.url
        return None

    @property
    def is_system_admin(self):
        return self.is_superuser

    @property
    def is_lms_admin(self):
        return self.is_superuser or self.role == self.Role.EMPLOYEE

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"