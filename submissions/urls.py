#  submissions/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.submission_list, name='submission_list'),
    path('assignment/<int:assignment_id>/submit/', views.submission_create, name='submission_create'),
    path('<int:pk>/', views.submission_detail, name='submission_detail'), 
    path('my-submissions/', views.student_submissions_dashboard, name='student_submissions_dashboard'),
    path('<int:pk>/grade/', views.submission_grade, name='submission_grade'),
    path('<int:pk>/delete/', views.submission_delete, name='submission_delete'), 
]
