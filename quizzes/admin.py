from django.contrib import admin
from .models import Choice, Question, QuestionBankChoice, QuestionBankItem, Quiz, QuizAttempt, StudentAnswer


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0


class QuestionBankChoiceInline(admin.TabularInline):
    model = QuestionBankChoice
    extra = 2


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'course', 'status', 'question_count', 'attempt_count', 'created_by', 'created_at']
    list_filter = ['status', 'course']
    search_fields = ['title', 'description', 'course__title']
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'quiz', 'text', 'question_type', 'points']
    list_filter = ['question_type', 'quiz']
    search_fields = ['text']
    inlines = [ChoiceInline]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['id', 'quiz', 'student', 'score', 'is_completed', 'is_auto_submitted', 'started_at']
    list_filter = ['is_completed', 'is_auto_submitted', 'quiz']
    search_fields = ['student__user__username', 'quiz__title']


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'attempt', 'question', 'is_correct']
    list_filter = ['is_correct']


@admin.register(QuestionBankItem)
class QuestionBankItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'text', 'course', 'question_type', 'points', 'created_by', 'created_at']
    list_filter = ['question_type', 'course']
    search_fields = ['text', 'course__title']
    inlines = [QuestionBankChoiceInline]
