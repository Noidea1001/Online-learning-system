# enrollments/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.enrollment_list, name='enrollment_list'),
    path('course/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('course/<int:course_id>/pay/', views.pay_course, name='pay_course'),
    path('add/', views.enrollment_create, name='enrollment_create'), 
    path('<int:pk>/', views.enrollment_detail, name='enrollment_detail'),
    path('<int:pk>/update/', views.enrollment_update, name='enrollment_update'),
    path('<int:pk>/delete/', views.enrollment_delete, name='enrollment_delete'),
    path('<int:pk>/toggle-payment/', views.toggle_payment_status, name='toggle_enrollment_payment'),
]
