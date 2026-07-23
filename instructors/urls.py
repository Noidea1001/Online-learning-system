# instructors/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.instructor_list, name='instructor_list'),
    path('create/', views.instructor_create_view, name='instructor_create'),
    path('<int:pk>/', views.instructor_detail, name='instructor_detail'),
    path('<int:pk>/update/', views.instructor_update, name='instructor_update'),
    path('<int:pk>/delete/', views.instructor_delete, name='instructor_delete'),
]
