# dashboard/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('calendar/', views.calendar_view, name='calendar_view'),
    path('analytics/api/', views.dashboard_analytics_api, name='dashboard_analytics_api'),
]
