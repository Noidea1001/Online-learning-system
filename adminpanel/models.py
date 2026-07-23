# adminpanel/models.py
# This app intentionally has no models of its own besides the audit trail,
# which is generic on purpose: it provides a custom front-end on top of the
# existing users.User model and Django's built-in auth Group / Permission
# models, plus a system-wide activity log for everything else.

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = 'CREATE', 'Created'
        UPDATE = 'UPDATE', 'Updated'
        DELETE = 'DELETE', 'Deleted'
        LOGIN = 'LOGIN', 'Logged In'
        LOGIN_FAILED = 'LOGIN_FAILED', 'Failed Login'

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text="Who performed the action. Blank for system/anonymous events.",
    )
    action = models.CharField(max_length=20, choices=Action.choices)

    # Generic link to the affected object (Course, Student, Enrollment, ...).
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey('content_type', 'object_id')

    # Snapshot of str(instance) at the time of the action, so the log still
    # reads clearly even after the target row has been deleted.
    object_repr = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        who = self.actor.username if self.actor else 'System'
        return f"{who} {self.get_action_display()} {self.object_repr}"

    @property
    def model_label(self):
        return self.content_type.model.title() if self.content_type else '—'
