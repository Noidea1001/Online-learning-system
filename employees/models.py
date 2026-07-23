# employees/models.py
from django.conf import settings
from django.db import models

class Employee(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='employee_profile'
    )
    image = models.ImageField(upload_to='employees/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=[('active', 'Active'), ('inactive', 'Inactive')], default='active')
    
    department = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    hire_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.user.username
