# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from students.models import Student
from instructors.models import Instructor
from employees.models import Employee

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_role_profile(sender, instance, created, **kwargs):
    if not created or instance.is_superuser:
        return

    if instance.role == 'STUDENT':
        Student.objects.get_or_create(user=instance)

    elif instance.role == 'INSTRUCTOR':
        Instructor.objects.get_or_create(user=instance)

    elif instance.role == 'EMPLOYEE':
        Employee.objects.get_or_create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_role_profile(sender, instance, created, **kwargs):

    if created or instance.is_superuser:
        return

    if instance.role == 'STUDENT':
        profile = getattr(instance, 'student_profile', None)
        if profile and profile.pk:
            profile.save()
        else:
            Student.objects.get_or_create(user=instance)

    elif instance.role == 'INSTRUCTOR':
        profile = getattr(instance, 'instructor_profile', None)
        if profile and profile.pk:
            profile.save()
        else:
            Instructor.objects.get_or_create(user=instance)

    elif instance.role == 'EMPLOYEE':
        profile = getattr(instance, 'employee_profile', None)
        if profile and profile.pk:
            profile.save()
        else:
            Employee.objects.get_or_create(user=instance)
