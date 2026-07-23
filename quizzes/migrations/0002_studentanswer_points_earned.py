from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentanswer',
            name='points_earned',
            field=models.DecimalField(
                max_digits=6, decimal_places=2, default=0,
                help_text="Actual points awarded. Can be a fraction of the question's points for partially-correct multiple choice answers.",
            ),
        ),
        migrations.AlterField(
            model_name='studentanswer',
            name='is_correct',
            field=models.BooleanField(default=False, help_text='Fully correct — all points earned.'),
        ),
    ]
