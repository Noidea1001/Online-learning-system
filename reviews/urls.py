from django.urls import path
from . import views

urlpatterns = [
    path('', views.review_list, name='review_list'),
    path('course/<int:course_id>/add/', views.review_create, name='review_create'),
    path('<int:pk>/approve/', views.review_approve, name='review_approve'),
    path('reviews/<int:pk>/', views.ReviewDetailView.as_view(), name='review_detail'),
    path('<int:pk>/delete/', views.review_delete, name='review_delete'), 
]
