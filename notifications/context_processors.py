from .models import Notification
from django.db.utils import OperationalError, ProgrammingError
from django.db import connection

def _ensure_notification_schema():
    try:
        from django.core.management import call_command
        call_command('migrate', 'notifications', interactive=False)
    except Exception:
        pass

    try:
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(notifications_notification)")
            columns = [row[1] for row in cursor.fetchall()]
            if columns and 'notification_type' not in columns:
                cursor.execute("ALTER TABLE notifications_notification ADD COLUMN notification_type varchar(20) DEFAULT 'SYSTEM'")

            cursor.execute("PRAGMA table_info(users_user)")
            u_columns = [row[1] for row in cursor.fetchall()]
            if u_columns and 'profile_picture' not in u_columns:
                cursor.execute("ALTER TABLE users_user ADD COLUMN profile_picture varchar(100) DEFAULT NULL")
    except Exception:
        pass

def notifications_processor(request):
    if request.user.is_authenticated:
        try:
            unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
            latest_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:5]
            return {
                'unread_notifications_count': unread_count,
                'latest_notifications': latest_notifications
            }
        except (OperationalError, ProgrammingError):
            _ensure_notification_schema()
            try:
                unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
                latest_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:5]
                return {
                    'unread_notifications_count': unread_count,
                    'latest_notifications': latest_notifications
                }
            except Exception:
                return {
                    'unread_notifications_count': 0,
                    'latest_notifications': []
                }
        except Exception:
            return {
                'unread_notifications_count': 0,
                'latest_notifications': []
            }
    return {
        'unread_notifications_count': 0,
        'latest_notifications': []
    }
