# Generated migration

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('quiz_game', '0002_levelprogress_generated_questions_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='GameQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_text', models.TextField()),
                ('option_a', models.CharField(max_length=500)),
                ('option_b', models.CharField(max_length=500)),
                ('option_c', models.CharField(max_length=500)),
                ('option_d', models.CharField(max_length=500)),
                ('correct_answer', models.CharField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], max_length=1)),
                ('explanation', models.TextField(blank=True)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('level_progress', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='quiz_game.levelprogress')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.AddIndex(
            model_name='gamequestion',
            index=models.Index(fields=['level_progress', 'order'], name='quiz_game_g_level_p_idx'),
        ),
    ]
