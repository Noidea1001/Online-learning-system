from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications_list, name='notifications_list'),
    path('<int:pk>/read/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('mark-all-read/', views.mark_all_notifications_as_read, name='mark_all_notifications_as_read'),
    path('<int:pk>/delete/', views.delete_notification, name='delete_notification'),
]
