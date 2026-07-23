# Generated for the question bank feature

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0003_question_sample_answer_quizattempt_needs_grading_and_more'),
        ('courses', '0006_tag_slug'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionBankItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('question_type', models.CharField(
                    choices=[
                        ('SINGLE', 'Single Choice'),
                        ('MULTIPLE', 'Multiple Choice'),
                        ('TRUE_FALSE', 'True / False'),
                        ('SHORT_ANSWER', 'Short Answer'),
                    ],
                    default='SINGLE', max_length=15,
                )),
                ('sample_answer', models.TextField(
                    blank=True,
                    help_text='Optional model answer shown to instructors while grading short answers.',
                )),
                ('points', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('course', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='question_bank_items', to='courses.course',
                )),
                ('created_by', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='bank_questions_created', to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='QuestionBankChoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=500)),
                ('is_correct', models.BooleanField(default=False)),
                ('order', models.PositiveIntegerField(default=0)),
                ('item', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='choices', to='quizzes.questionbankitem',
                )),
            ],
            options={'ordering': ['order', 'id']},
        ),
    ]
