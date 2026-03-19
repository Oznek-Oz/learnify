# quizz/models.py ← ajoute le champ status

from django.db import models
from courses.models import Course


class Quiz(models.Model):

    class Status(models.TextChoices):
        PENDING    = 'pending',    'En attente'
        GENERATING = 'generating', 'Génération en cours'
        READY      = 'ready',      'Prêt'
        FAILED     = 'failed',     'Échec'

    class Difficulty(models.TextChoices):
        EASY   = 'easy',   'Facile'
        MEDIUM = 'medium', 'Moyen'
        HARD   = 'hard',   'Difficile'

    course     = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='quizzes'
    )
    title      = models.CharField(max_length=255)
    difficulty = models.CharField(
        max_length=10,
        choices=Difficulty.choices,
        default=Difficulty.MEDIUM
    )
    topic      = models.CharField(max_length=255, blank=True)
    status     = models.CharField(        # ← nouveau
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.course.title}"


class Question(models.Model):
    quiz            = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_text   = models.TextField()
    option_a        = models.CharField(max_length=500)
    option_b        = models.CharField(max_length=500)
    option_c        = models.CharField(max_length=500)
    option_d        = models.CharField(max_length=500)
    correct_answer  = models.CharField(
        max_length=1,
        choices=[('A','A'),('B','B'),('C','C'),('D','D')]
    )
    explanation     = models.TextField(blank=True)
    order           = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']