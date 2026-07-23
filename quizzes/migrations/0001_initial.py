from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0001_initial'),
        ('courses', '0006_tag_slug'),
        ('lessons', '0002_alter_lesson_options_alter_lesson_description_and_more'),
        ('students', '0003_student_bio_student_gender_student_phone_number_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, help_text='Instructions shown to students before they start.')),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('PUBLISHED', 'Published')], default='DRAFT', max_length=10)),
                ('time_limit_minutes', models.PositiveIntegerField(blank=True, help_text='Leave blank for an untimed test.', null=True)),
                ('max_attempts', models.PositiveIntegerField(default=1)),
                ('passing_score', models.PositiveIntegerField(blank=True, help_text='Percentage required to pass (optional).', null=True)),
                ('shuffle_questions', models.BooleanField(default=False)),
                ('due_date', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quizzes', to='courses.course')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quizzes_created', to=settings.AUTH_USER_MODEL)),
                ('lesson', models.ForeignKey(blank=True, help_text='Optional — attach to a specific lesson, or leave blank for a course-wide test.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='quizzes', to='lessons.lesson')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(default=0)),
                ('text', models.TextField()),
                ('question_type', models.CharField(choices=[('SINGLE', 'Single Choice'), ('MULTIPLE', 'Multiple Choice'), ('TRUE_FALSE', 'True / False')], default='SINGLE', max_length=10)),
                ('points', models.PositiveIntegerField(default=1)),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='quizzes.quiz')),
            ],
            options={'ordering': ['order', 'id']},
        ),
        migrations.CreateModel(
            name='Choice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=500)),
                ('is_correct', models.BooleanField(default=False)),
                ('order', models.PositiveIntegerField(default=0)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='choices', to='quizzes.question')),
            ],
            options={'ordering': ['order', 'id']},
        ),
        migrations.CreateModel(
            name='QuizAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('score', models.DecimalField(blank=True, decimal_places=2, help_text='Percentage score.', max_digits=5, null=True)),
                ('is_completed', models.BooleanField(default=False)),
                ('is_auto_submitted', models.BooleanField(default=False, help_text='True if the timer ran out.')),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='quizzes.quiz')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quiz_attempts', to='students.student')),
            ],
            options={'ordering': ['-started_at']},
        ),
        migrations.CreateModel(
            name='StudentAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_correct', models.BooleanField(default=False)),
                ('attempt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='quizzes.quizattempt')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_answers', to='quizzes.question')),
                ('selected_choices', models.ManyToManyField(blank=True, related_name='selected_in_answers', to='quizzes.choice')),
            ],
            options={'ordering': ['question__order']},
        ),
    ]
