from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from courses.models import Course
from config.app_config import QUIZ_GAME_MAX_UNLOCKED_LEVELS


# Configuration des niveaux (nombres de quiz par niveau)
LEVEL_CONFIG = [
    {'number': 1, 'title': 'Niveau 1 - Débutant', 'difficulty': 'easy', 'quiz_count': 5},
    {'number': 2, 'title': 'Niveau 2', 'difficulty': 'easy', 'quiz_count': 7},
    {'number': 3, 'title': 'Niveau 3', 'difficulty': 'easy', 'quiz_count': 9},
    {'number': 4, 'title': 'Niveau 4', 'difficulty': 'medium', 'quiz_count': 11},
    {'number': 5, 'title': 'Niveau 5', 'difficulty': 'medium', 'quiz_count': 13},
    {'number': 6, 'title': 'Niveau 6', 'difficulty': 'medium', 'quiz_count': 15},
    {'number': 7, 'title': 'Niveau 7', 'difficulty': 'medium', 'quiz_count': 16},
    {'number': 8, 'title': 'Niveau 8 - Avancé', 'difficulty': 'hard', 'quiz_count': 17},
    {'number': 9, 'title': 'Niveau 9', 'difficulty': 'hard', 'quiz_count': 18},
    {'number': 10, 'title': 'Niveau 10 - Expert', 'difficulty': 'hard', 'quiz_count': 20},
]


class Level(models.Model):
    class Difficulty(models.TextChoices):
        EASY = 'easy', 'Facile'
        MEDIUM = 'medium', 'Moyen'
        HARD = 'hard', 'Difficile'

    number = models.PositiveSmallIntegerField(unique=True)
    title = models.CharField(max_length=255)
    difficulty = models.CharField(
        max_length=10,
        choices=Difficulty.choices,
        default=Difficulty.EASY
    )
    quiz_count = models.PositiveSmallIntegerField(default=5)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['number']
        indexes = [
            models.Index(fields=['number']),
            models.Index(fields=['difficulty']),
        ]

    def __str__(self):
        return f"Niveau {self.number} — {self.title}"


class QuizGameProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_game_progresses'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='quiz_game_progresses'
    )
    topic = models.CharField(max_length=255, blank=True)
    unlocked_levels = models.ManyToManyField(
        Level,
        related_name='unlocked_in_progress',
        blank=True
    )
    completed_levels = models.ManyToManyField(
        Level,
        related_name='completed_in_progress',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = [['user', 'course', 'topic']]
        indexes = [
            models.Index(fields=['user', 'course']),
            models.Index(fields=['course', 'topic']),
        ]

    def __str__(self):
        return f"Progression de {self.user} — {self.course.title} ({self.topic or 'général'})"

    def ensure_initialized(self):
        """
        Initialise la progression avec les 10 niveaux et déclenche 
        la génération des quiz en arrière-plan.
        """
        # Créer les 10 niveaux s'ils n'existent pas globalement
        for config in LEVEL_CONFIG:
            Level.objects.get_or_create(
                number=config['number'],
                defaults={
                    'title': config['title'],
                    'difficulty': config['difficulty'],
                    'quiz_count': config['quiz_count'],
                    'is_active': True,
                }
            )

        # Déverrouiller le niveau 1 si nécessaire
        first_level = Level.objects.filter(number=1, is_active=True).first()
        if first_level and not self.unlocked_levels.filter(pk=first_level.pk).exists():
            self.unlocked_levels.add(first_level)

        # Créer les LevelProgress pour tous les niveaux
        for level in Level.objects.order_by('number'):
            LevelProgress.objects.get_or_create(
                user_progress=self,
                level=level,
                defaults={
                    'required_quiz_count': level.quiz_count,
                    'status': LevelProgress.Status.PENDING,
                }
            )

        # Lancer la génération pour tous les niveaux débloqués qui sont en attente
        for unlocked_level in self.unlocked_levels.order_by('number'):
            level_progress = LevelProgress.objects.filter(
                user_progress=self,
                level=unlocked_level,
                status=LevelProgress.Status.PENDING,
            ).first()
            if level_progress:
                level_progress.status = LevelProgress.Status.GENERATING
                level_progress.save(update_fields=['status'])
                from .tasks import generate_level_quizzes_task
                generate_level_quizzes_task.delay(
                    self.id,
                    unlocked_level.number,
                    self.topic
                )

    def _trim_unlocked_levels(self):
        unlocked = list(self.unlocked_levels.order_by('number'))
        overflow = len(unlocked) - QUIZ_GAME_MAX_UNLOCKED_LEVELS
        if overflow > 0:
            for level in unlocked[:overflow]:
                self.unlocked_levels.remove(level)

    def unlock_level_number(self, number):
        if number < 1 or number > 10:
            return None
        if self.completed_levels.filter(number=number).exists():
            return None
        level = Level.objects.filter(number=number, is_active=True).first()
        if level:
            self.unlocked_levels.add(level)
            self._trim_unlocked_levels()
            level_progress = LevelProgress.objects.filter(
                user_progress=self,
                level=level,
                status=LevelProgress.Status.PENDING,
            ).first()
            if level_progress:
                level_progress.status = LevelProgress.Status.GENERATING
                level_progress.save(update_fields=['status'])
                from .tasks import generate_level_quizzes_task
                generate_level_quizzes_task.delay(
                    self.id,
                    level.number,
                    self.topic
                )
        return level

    def complete_level(self, level):
        if not self.unlocked_levels.filter(pk=level.pk).exists():
            return False
        self.unlocked_levels.remove(level)
        self.completed_levels.add(level)
        self.unlock_level_number(level.number + 1)
        self.unlock_level_number(level.number + 2)
        self._trim_unlocked_levels()
        self.save()
        return True

    def is_level_unlocked(self, level):
        return self.unlocked_levels.filter(pk=level.pk).exists()

    def current_unlocked_numbers(self):
        return list(self.unlocked_levels.order_by('number').values_list('number', flat=True))

    def current_completed_numbers(self):
        return list(self.completed_levels.order_by('number').values_list('number', flat=True))


class LevelProgress(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'En attente'
        GENERATING = 'generating', 'Génération en cours'
        READY = 'ready', 'Prêt'
        IN_PROGRESS = 'in_progress', 'En cours'
        PASSED = 'passed', 'Validé'
        FAILED = 'failed', 'Échoué'

    user_progress = models.ForeignKey(
        QuizGameProgress,
        on_delete=models.CASCADE,
        related_name='level_progresses'
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name='level_progresses'
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING
    )
    completed_quiz_count = models.PositiveSmallIntegerField(default=0)
    required_quiz_count = models.PositiveSmallIntegerField(default=5)
    generated_questions = models.PositiveSmallIntegerField(default=0)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    unlocked_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level__number']
        unique_together = [['user_progress', 'level']]
        indexes = [
            models.Index(fields=['user_progress', 'level']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.level} — {self.user_progress.user.email} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.required_quiz_count and self.level_id:
            self.required_quiz_count = self.level.quiz_count
        if self.status == self.Status.IN_PROGRESS and self.unlocked_at is None:
            self.unlocked_at = timezone.now()
        if self.status == self.Status.PASSED and self.completed_at is None:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)


class GameQuestion(models.Model):
    """
    Questions générées pour un niveau du quiz game.
    Créées lors de la génération du niveau et utilisées pour jouer.
    """
    level_progress = models.ForeignKey(
        LevelProgress,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_text = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_answer = models.CharField(
        max_length=1,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]
    )
    explanation = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['level_progress', 'order']),
        ]

    def __str__(self):
        return f"Q{self.order} — {self.level_progress.level.title}"
