from .models import Notification

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
    except Exception:
        # Safe fallback if tables don't exist yet
        return {
            'unread_notifications_count': 0,
            'latest_notifications': []
        }