# flashcards/models.py

from django.db import models
from courses.models import Course


class FlashcardDeck(models.Model):
    """
    Un deck = une collection de fiches sur un sujet précis.
    Ex: "Fiches Thermodynamique — Cours de Physique"
    """
    class Status(models.TextChoices):
        PENDING     = 'pending',     'En attente'
        GENERATING  = 'generating',  'Génération en cours'
        IN_PROGRESS = 'in_progress', 'En cours'
        READY       = 'ready',       'Prêt'
        FAILED      = 'failed',      'Échec'

    course     = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='decks'
    )
    title      = models.CharField(max_length=255)
    topic      = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status     = models.CharField(      
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', 'status']),  # Requêtes par cours + status
            models.Index(fields=['course', '-created_at']),  # Listes récentes par cours
        ]

    def __str__(self):
        return f"{self.title} — {self.course.title}"


class Flashcard(models.Model):
    """
    Une fiche = recto (question) + verso (réponse).
    Système de révision espacée avec les niveaux de maîtrise.
    """
    class Mastery(models.TextChoices):
        NEW        = 'new',        'Nouvelle'
        LEARNING   = 'learning',   'En apprentissage'
        REVIEWING  = 'reviewing',  'En révision'
        MASTERED   = 'mastered',   'Maîtrisée'

    deck       = models.ForeignKey(
        FlashcardDeck,
        on_delete=models.CASCADE,
        related_name='flashcards'
    )
    front      = models.TextField()   # Question / Concept
    back       = models.TextField()   # Réponse / Définition
    hint       = models.TextField(    # Indice optionnel
        blank=True,
        help_text="Indice pour aider à trouver la réponse"
    )
    mastery    = models.CharField(
        max_length=15,
        choices=Mastery.choices,
        default=Mastery.NEW
    )
    order      = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Fiche {self.order} — {self.deck.title}"