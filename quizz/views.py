# quizz/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from config.app_config import QUIZ_SEARCH_RESULTS
from config.throttles import GenerationThrottle
from config.pagination import LargePagination
from courses.models import Course
from courses.vector_store import search_similar_chunks
from .models import Quiz, Question
from .serializers import QuizSerializer, GenerateQuizSerializer
from .tasks import generate_quiz_task
import logging

logger = logging.getLogger(__name__)


class GenerateQuizView(APIView):
    """
    POST /api/quiz/generate/
    Crée le quiz immédiatement et lance la génération en arrière-plan
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [GenerationThrottle]

    def post(self, request):
        serializer = GenerateQuizSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # 1. Vérifie que le cours appartient à l'utilisateur
        course = get_object_or_404(
            Course, id=data['course_id'], owner=request.user
        )

        # 2. Vérifie que le cours est prêt
        if course.status != Course.Status.READY:
            return Response(
                {"error": f"Cours non prêt. Statut : {course.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Recherche sémantique RAG
        topic = data.get('topic', '').strip()
        if topic:
            # Recherche par sujet spécifique
            chunks = search_similar_chunks(
                course_id = course.id,
                query     = topic,
                n_results = QUIZ_SEARCH_RESULTS
            )
        else:
            # Si pas de sujet, utiliser tout le contenu du cours
            # On récupère tous les chunks du cours via ChromaDB
            from courses.vector_store import get_chroma_client
            collection = get_chroma_client().get_or_create_collection(f"course_{course.id}")
            results = collection.get()
            chunks = results.get('documents', [])[:QUIZ_SEARCH_RESULTS] if results.get('documents') else []

        if not chunks:
            return Response(
                {"error": "Aucun contenu trouvé dans ce cours."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 4. Crée le quiz vide IMMÉDIATEMENT en base
        quiz_title = f"Quiz — {topic}" if topic else f"Quiz — {course.title}"
        quiz = Quiz.objects.create(
            course     = course,
            title      = quiz_title,
            difficulty = data['difficulty'],
            topic      = topic or '',  # Vide si pas de sujet
            status     = Quiz.Status.PENDING   # ← statut initial
        )

        # 5. Lance la génération en arrière-plan via Celery
        generate_quiz_task.delay(
            quiz_id       = quiz.id,
            chunks        = chunks,
            topic         = data.get('topic', ''),
            difficulty    = data['difficulty'],
            num_questions = data['num_questions']
        )

        # 6. Répond IMMÉDIATEMENT sans attendre Gemini
        return Response(
            QuizSerializer(quiz).data,
            status=status.HTTP_202_ACCEPTED   # 202 = "Accepté, traitement en cours"
        )


class QuizListView(generics.ListAPIView):
    """
    GET /api/quiz/
    Liste tous les quiz de l'utilisateur connecté
    """
    serializer_class   = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class   = LargePagination

    def get_queryset(self):
        return Quiz.objects.filter(
            course__owner=self.request.user
        ).prefetch_related('questions')


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/quiz/<id>/   → détail d'un quiz (utilisé pour le polling)
    PATCH  /api/quiz/<id>/   → mise à jour partielle du statut ou des métadonnées
    DELETE /api/quiz/<id>/   → supprimer un quiz
    """
    serializer_class   = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(
            course__owner=self.request.user
        ).prefetch_related('questions')



"""""
## Ce qui a changé vs l'ancien fichier
```
Avant :
→ Gemini générait les questions dans la vue
→ L'utilisateur attendait 60s bloqué

Après :
→ Quiz créé en base immédiatement (status: pending)
→ generate_quiz_task.delay() lance Celery
→ Réponse en 50ms avec status 202 ✅
→ Celery génère en arrière-plan"""