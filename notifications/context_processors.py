from .models import Notification
from django.db.utils import OperationalError, ProgrammingError

def notifications_processor(request):
    if not request.user.is_authenticated:
        return {
            'unread_notifications_count': 0,
            'latest_notifications': []
        }

    try:
        unread_count = Notification.objects.filter(
            recipient=request.user, 
            is_read=False
        ).count()
        
        latest_notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')[:5]

        return {
            'unread_notifications_count': unread_count,
            'latest_notifications': latest_notifications
        }

    except (OperationalError, ProgrammingError, Exception):
        # Graceful fallback
        return {
            'unread_notifications_count': 0,
            'latest_notifications': []
        }