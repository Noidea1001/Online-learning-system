# quizzes/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Staff (admin / employee / instructor)
    path('', views.quiz_list, name='quiz_list'),
    path('add/', views.quiz_builder, name='quiz_builder'),
    path('<int:pk>/edit/', views.quiz_builder, name='quiz_builder_edit'),
    path('<int:pk>/', views.quiz_detail, name='quiz_detail'),
    path('<int:pk>/export/', views.quiz_export_results, name='quiz_export_results'),
    path('<int:pk>/grade/', views.quiz_grade_queue, name='quiz_grade_queue'),
    path('answer/<int:answer_id>/grade/', views.quiz_grade_answer, name='quiz_grade_answer'),
    path('<int:pk>/delete/', views.quiz_delete, name='quiz_delete'),
    path('<int:pk>/duplicate/', views.quiz_duplicate, name='quiz_duplicate'),

    # Question bank
    path('bank/', views.question_bank_list, name='question_bank_list'),
    path('bank/items/', views.question_bank_items, name='question_bank_items'),
    path('bank/save/', views.question_bank_save, name='question_bank_save'),
    path('bank/<int:pk>/delete/', views.question_bank_delete, name='question_bank_delete'),

    # Student
    path('my/', views.student_quiz_list, name='student_quiz_list'),
    path('<int:pk>/take/', views.quiz_take, name='quiz_take'),
    path('attempt/<int:pk>/autosave/', views.quiz_autosave, name='quiz_autosave'),
    path('attempt/<int:pk>/result/', views.quiz_result, name='quiz_result'),
]
