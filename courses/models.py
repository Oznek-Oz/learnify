# courses/models.py

from django.db import models
from django.conf import settings

# fonction pour définir le chemin de stockage des fichiers uploadés par les utilisateurs (PDF, images) en les organisant par utilisateur
def course_upload_path(instance, filename):
    """
    Les fichiers seront stockés dans :
    media/courses/<user_id>/<filename>
    """
    return f'courses/{instance.owner.id}/{filename}'

# Modèle Course pour représenter les cours uploadés par les utilisateurs. Chaque cours est lié à un utilisateur (owner) et contient des informations sur le titre, la description, le fichier uploadé, le type de fichier, le statut du traitement, ainsi que les timestamps de création et de mise à jour.
class Course(models.Model):

    # Statuts possibles d'un cours (pipeline RAG)
    class Status(models.TextChoices):
        UPLOADED    = 'uploaded',    'Uploadé'
        PROCESSING  = 'processing',  'En traitement'
        READY       = 'ready',       'Prêt'
        FAILED      = 'failed',      'Échec'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,       # si user supprimé → ses cours aussi
        related_name='courses'
    )
    title       = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file        = models.FileField(upload_to=course_upload_path)
    file_type   = models.CharField(max_length=10)   # 'pdf' ou 'image'
    status      = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']   # les plus récents en premier

    def __str__(self):
        return f"{self.title} ({self.owner.email})"
    

class CourseChunk(models.Model):
    """
    Représente un morceau de texte extrait du cours.
    Chaque chunk aura son embedding stocké dans ChromaDB.
    """
    course     = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='chunks'
    )
    content    = models.TextField()          # le texte du chunk
    page_number = models.IntegerField(default=0)  # page d'origine
    chunk_index = models.IntegerField()      # position dans le cours
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['chunk_index']

    def __str__(self):
        return f"Chunk {self.chunk_index} — {self.course.title}"