# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='home'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile_edit, name='profile_edit'),
    path('dashboard/redirect/', views.dashboard_redirect, name='dashboard_redirect'),
]