# online_learning_system/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views as project_views

urlpatterns = [
    path('offline/', project_views.offline, name='offline'),
    path('sw.js', project_views.service_worker, name='service_worker'),

    path('', include('users.urls')),          
    path('dashboard/', include('dashboard.urls')),
    path('employees/', include('employees.urls')),
    path('control-panel/', include('adminpanel.urls')),
    # path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')), 
    
    path('students/', include('students.urls')),
    path('instructors/', include('instructors.urls')),
    path('category/', include('category.urls')), 
    path('courses/', include('courses.urls')),
    path('lessons/', include('lessons.urls')),
    path('enrollments/', include('enrollments.urls')),
    path('assignments/', include('assignments.urls')),
    path('submissions/', include('submissions.urls')),
    path('reviews/', include('reviews.urls')),
    path('quizzes/', include('quizzes.urls')),
    path('notifications/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Auto-apply database migrations and schema checks on startup to support notifications
try:
    import sys
    if 'makemigrations' not in sys.argv and 'migrate' not in sys.argv:
        from notifications.context_processors import _ensure_notification_schema
        _ensure_notification_schema()
except Exception as e:
    sys.stderr.write(f"Auto-migration warning: {e}\n")

