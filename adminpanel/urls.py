# adminpanel/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.control_center, name='adminpanel_home'),

    path('users/', views.user_list, name='adminpanel_user_list'),
    path('users/<int:pk>/', views.user_permissions_detail, name='adminpanel_user_detail'),

    path('groups/', views.group_list, name='adminpanel_group_list'),
    path('groups/create/', views.group_create, name='adminpanel_group_create'),
    path('groups/<int:pk>/', views.group_detail, name='adminpanel_group_detail'),
    path('groups/<int:pk>/delete/', views.group_delete, name='adminpanel_group_delete'),

    path('audit-log/', views.audit_log_list, name='adminpanel_audit_log'),
]
