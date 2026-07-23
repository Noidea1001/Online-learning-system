from django.urls import path
from .views import (
    CourseListView, 
    CourseDetailView,
    course_create, 
    course_update, 
    course_delete,
    tag_list,
    tag_create,
    tag_update,
    tag_delete
)

urlpatterns = [
    # Course List (Main page with filters)
    path('', CourseListView.as_view(), name='course_list'),
    
    # Course Detail (with Login + Enrollment check)
    path('<int:pk>/', CourseDetailView.as_view(), name='course_detail'),
    # CRUD Operations
    path('create/', course_create, name='course_create'),
    path('<int:pk>/update/', course_update, name='course_update'),
    path('<int:pk>/delete/', course_delete, name='course_delete'),
    
    # Tag Operations
    path('tags/', tag_list, name='tag_list'),
    path('tags/add/', tag_create, name='tag_create'),
    path('tags/<int:pk>/update/', tag_update, name='tag_update'),
    path('tags/<int:pk>/delete/', tag_delete, name='tag_delete'),
]
