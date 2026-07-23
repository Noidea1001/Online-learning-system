# lessons/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.lesson_list, name='lesson_list'), 
    
    path('add/', views.lesson_create, name='lesson_create'),
    path('<int:pk>/', views.lesson_detail, name='lesson_detail'),
    path('<int:pk>/update/', views.lesson_update, name='lesson_update'),
    path('<int:pk>/delete/', views.lesson_delete, name='lesson_delete'),
    path('<int:pk>/toggle-complete/', views.toggle_lesson_completion, name='toggle_lesson_completion'),
]
