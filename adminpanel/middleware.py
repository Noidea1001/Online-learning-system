# adminpanel/middleware.py
"""
Signal handlers (post_save / post_delete) don't receive the current request,
so they have no way to know *who* triggered a change. This middleware stashes
the current request's user and IP address in a thread-local, which the audit
log signal handlers in adminpanel/signals.py read from.
"""
import threading

_local = threading.local()


def get_current_user():
    return getattr(_local, 'user', None)


def get_current_ip():
    return getattr(_local, 'ip', None)


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class CurrentUserMiddleware:
    """Must be placed after AuthenticationMiddleware in settings.MIDDLEWARE."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.user = getattr(request, 'user', None)
        _local.ip = _client_ip(request)
        try:
            response = self.get_response(request)
        finally:
            _local.user = None
            _local.ip = None
        return response
