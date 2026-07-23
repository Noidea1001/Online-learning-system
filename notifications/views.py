from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.utils import OperationalError, ProgrammingError
from .models import Notification

@login_required
def notifications_list(request):
    filter_type = request.GET.get('filter', 'all')
    try:
        notifications_qs = Notification.objects.filter(recipient=request.user)

        if filter_type == 'unread':
            notifications_qs = notifications_qs.filter(is_read=False)
        elif filter_type == 'read':
            notifications_qs = notifications_qs.filter(is_read=True)
    except (OperationalError, ProgrammingError):
        try:
            from django.core.management import call_command
            call_command('migrate', 'notifications', interactive=False)
            notifications_qs = Notification.objects.filter(recipient=request.user)
            if filter_type == 'unread':
                notifications_qs = notifications_qs.filter(is_read=False)
            elif filter_type == 'read':
                notifications_qs = notifications_qs.filter(is_read=True)
        except Exception:
            notifications_qs = Notification.objects.none()

    return render(request, 'notifications/notifications_list.html', {
        'notifications': notifications_qs,
        'filter_type': filter_type,
    })

@login_required
def mark_notification_as_read(request, pk):
    try:
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        if not notification.is_read:
            notification.is_read = True
            notification.save()
        
        if notification.url:
            return redirect(notification.url)
    except Exception:
        pass
    return redirect('notifications_list')

@login_required
def mark_all_notifications_as_read(request):
    try:
        unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False)
        count = unread_notifications.count()
        if count > 0:
            unread_notifications.update(is_read=True)
            messages.success(request, f"Marked {count} notifications as read.")
        else:
            messages.info(request, "No unread notifications to mark as read.")
    except Exception as e:
        messages.error(request, f"Could not update notifications: {e}")
    
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('notifications_list')

@login_required
def delete_notification(request, pk):
    try:
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.delete()
        messages.success(request, "Notification deleted.")
    except Exception:
        messages.error(request, "Could not delete notification.")
    
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('notifications_list')
