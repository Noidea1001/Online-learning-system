# quizzes/models.py
from django.conf import settings
from django.db import models
from django.utils import timezone


class Quiz(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PUBLISHED = 'PUBLISHED', 'Published'

    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='quizzes')
    lesson = models.ForeignKey(
        'lessons.Lesson', on_delete=models.CASCADE, related_name='quizzes',
        null=True, blank=True,
        help_text="Optional — attach to a specific lesson, or leave blank for a course-wide test.",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, help_text="Instructions shown to students before they start.")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='quizzes_created'
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)

    time_limit_minutes = models.PositiveIntegerField(
        null=True, blank=True, help_text="Leave blank for an untimed test."
    )
    max_attempts = models.PositiveIntegerField(default=1)
    passing_score = models.PositiveIntegerField(
        null=True, blank=True, help_text="Percentage required to pass (optional)."
    )
    shuffle_questions = models.BooleanField(default=False)
    due_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def question_count(self):
        return self.questions.count()

    @property
    def total_points(self):
        return self.questions.aggregate(total=models.Sum('points'))['total'] or 0

    @property
    def is_past_due(self):
        return bool(self.due_date and timezone.now() > self.due_date)

    @property
    def has_attempts(self):
        return self.attempts.exists()

    @property
    def attempt_count(self):
        return self.attempts.filter(is_completed=True).count()

    @property
    def average_score(self):
        completed = self.attempts.filter(is_completed=True, score__isnull=False)
        if not completed.exists():
            return None
        return round(sum(a.score for a in completed) / completed.count(), 1)

    @property
    def has_short_answer(self):
        return self.questions.filter(question_type=Question.Type.SHORT_ANSWER).exists()

    @property
    def pending_grading_count(self):
        return self.attempts.filter(is_completed=True, needs_grading=True).count()


class Question(models.Model):
    class Type(models.TextChoices):
        SINGLE = 'SINGLE', 'Single Choice'
        MULTIPLE = 'MULTIPLE', 'Multiple Choice'
        TRUE_FALSE = 'TRUE_FALSE', 'True / False'
        SHORT_ANSWER = 'SHORT_ANSWER', 'Short Answer'

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    order = models.PositiveIntegerField(default=0)
    text = models.TextField()
    question_type = models.CharField(max_length=15, choices=Type.choices, default=Type.SINGLE)
    sample_answer = models.TextField(
        blank=True, help_text="Optional model answer shown to instructors while grading short answers."
    )
    points = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.text[:60]

    @property
    def correct_choice_ids(self):
        return set(self.choices.filter(is_correct=True).values_list('id', flat=True))


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.text[:60]


class QuestionBankItem(models.Model):
    """
    A reusable question, scoped to a course, independent of any single
    Quiz. Deliberately opt-in and fully decoupled: saving a question here
    copies its data in, and pulling one into a quiz copies it back out as
    a normal Question. There's no live link either direction, so editing
    or deleting a bank item never touches quizzes that already used it,
    and editing a quiz question never touches the bank.
    """
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='question_bank_items')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='bank_questions_created'
    )
    text = models.TextField()
    question_type = models.CharField(max_length=15, choices=Question.Type.choices, default=Question.Type.SINGLE)
    sample_answer = models.TextField(
        blank=True, help_text="Optional model answer shown to instructors while grading short answers."
    )
    points = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.text[:60]


class QuestionBankChoice(models.Model):
    item = models.ForeignKey(QuestionBankItem, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.text[:60]


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='quiz_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Percentage score. Provisional (auto-graded questions only) until any short-answer questions are graded.",
    )
    is_completed = models.BooleanField(default=False)
    is_auto_submitted = models.BooleanField(default=False, help_text="True if the timer ran out.")
    needs_grading = models.BooleanField(
        default=False, help_text="True while this attempt has ungraded short-answer questions."
    )

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.student} — {self.quiz.title} ({self.score if self.score is not None else 'in progress'})"

    @property
    def passed(self):
        if self.quiz.passing_score is None or self.score is None or self.needs_grading:
            return None
        return self.score >= self.quiz.passing_score

    @property
    def deadline(self):
        """The timestamp this attempt must be submitted by, if the quiz is timed."""
        if not self.quiz.time_limit_minutes:
            return None
        return self.started_at + timezone.timedelta(minutes=self.quiz.time_limit_minutes)


class StudentAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='student_answers')
    selected_choices = models.ManyToManyField(Choice, blank=True, related_name='selected_in_answers')
    text_answer = models.TextField(blank=True, help_text="Free-text response for short-answer questions.")
    is_correct = models.BooleanField(default=False, help_text="Fully correct — all points earned.")
    points_earned = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        help_text="Actual points awarded. Can be a fraction of the question's points for partially-correct multiple choice answers.",
    )
    is_graded = models.BooleanField(
        default=True,
        help_text="False only for short-answer questions awaiting manual grading; auto-graded types are always True.",
    )
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_answers'
    )
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['question__order']

    def __str__(self):
        return f"Answer to Q{self.question_id} in attempt #{self.attempt_id}"
