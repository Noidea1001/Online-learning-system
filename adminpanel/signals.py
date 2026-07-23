# adminpanel/signals.py
"""
Centralised audit-trail wiring. Rather than sprinkling log_action() calls
through a dozen apps' views, we hook Django's post_save / post_delete
signals for the models worth tracking. This keeps the audit trail
consistent (every create/update/delete is caught, even from the Django
admin or a shell) and keeps the other apps free of audit-log concerns.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from assignments.models import Assignment
from category.models import Category
from courses.models import Course
from employees.models import Employee
from enrollments.models import Enrollment
from instructors.models import Instructor
from lessons.models import Lesson
from quizzes.models import Quiz
from reviews.models import Review
from students.models import Student
from submissions.models import Submission

from .models import AuditLog
from .utils import log_action

User = get_user_model()

TRACKED_MODELS = (
    Course, Category, Lesson, Assignment, Submission,
    Review, Enrollment, Student, Instructor, Employee, Group, Quiz,
)

# users/signals.py re-saves the matching Student/Instructor/Employee profile
# on *every* User save — including the harmless last_login-only save that
# fires on every login. Logging every one of those as "Updated" would flood
# the audit trail with noise, so these three are only logged on create/delete;
# genuine profile edits are still visible via the User's own UPDATE entry.
CREATE_DELETE_ONLY_MODELS = (Student, Instructor, Employee)


@receiver(post_save)
def _log_model_saved(sender, instance, created, **kwargs):
    if sender not in TRACKED_MODELS and sender is not User:
        return

    if sender is User:
        # Ignore the near-constant last_login-only save that happens on
        # every request/login — that path is already covered by the
        # dedicated LOGIN signal below and would otherwise flood the log.
        update_fields = kwargs.get('update_fields')
        if update_fields and set(update_fields) == {'last_login'}:
            return

    if sender in CREATE_DELETE_ONLY_MODELS and not created:
        return

    action = AuditLog.Action.CREATE if created else AuditLog.Action.UPDATE
    log_action(action, instance=instance)


@receiver(post_delete)
def _log_model_deleted(sender, instance, **kwargs):
    if sender not in TRACKED_MODELS and sender is not User:
        return
    log_action(AuditLog.Action.DELETE, instance=instance)


@receiver(m2m_changed, sender=Group.permissions.through)
def _log_group_permissions_changed(sender, instance, action, **kwargs):
    if action in ('post_add', 'post_remove', 'post_clear'):
        log_action(
            AuditLog.Action.UPDATE,
            instance=instance,
            description='Permissions updated',
        )


@receiver(user_logged_in)
def _log_user_logged_in(sender, request, user, **kwargs):
    log_action(AuditLog.Action.LOGIN, instance=user, actor=user)


@receiver(user_login_failed)
def _log_user_login_failed(sender, credentials, **kwargs):
    username = credentials.get('username', 'unknown')
    log_action(
        AuditLog.Action.LOGIN_FAILED,
        description=f'Failed login attempt for username "{username}"',
    )
