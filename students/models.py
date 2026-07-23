# students/models.py
from django.conf import settings
from django.db import models

class Student(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='student_profile'
    )
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='students/profiles/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True, help_text="Short biography or study goals.")
    
    date_of_birth = models.DateField(blank=True, null=True)
    enrolled_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        full_name = self.user.get_full_name()
        return full_name if full_name else self.user.username
