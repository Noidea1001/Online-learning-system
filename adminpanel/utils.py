# adminpanel/utils.py
from .middleware import get_current_ip, get_current_user


def log_action(action, instance=None, description='', actor=None):
    """
    Write one AuditLog row. Never raises — a broken audit write should
    never take down the request that triggered it.
    """
    from .models import AuditLog
    from django.contrib.contenttypes.models import ContentType

    try:
        kwargs = {
            'action': action,
            'actor': actor or get_current_user() or None,
            'ip_address': get_current_ip(),
            'description': description,
        }
        if kwargs['actor'] is not None and not getattr(kwargs['actor'], 'is_authenticated', True):
            kwargs['actor'] = None

        if instance is not None:
            kwargs['content_type'] = ContentType.objects.get_for_model(instance.__class__)
            kwargs['object_id'] = instance.pk
            kwargs['object_repr'] = str(instance)[:255]

        AuditLog.objects.create(**kwargs)
    except Exception:
        # Logging should be best-effort only.
        pass
