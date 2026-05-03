# flashcards/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from config.app_config import FLASHCARDS_RESULTS
from config.throttles import GenerationThrottle
from config.pagination import LargePagination
from courses.models import Course
from courses.vector_store import search_similar_chunks
from .models import FlashcardDeck, Flashcard
from .serializers import (
    FlashcardDeckSerializer,
    FlashcardSerializer,
    GenerateFlashcardsSerializer,
    UpdateMasterySerializer
)
from .tasks import generate_flashcards_task
import logging

logger = logging.getLogger(__name__)


class GenerateFlashcardsView(APIView):
    """
    POST /api/flashcards/generate/
    Crée le deck immédiatement et lance la génération en arrière-plan
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [GenerationThrottle]

    def post(self, request):
        serializer = GenerateFlashcardsSerializer(data=request.data)
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
                n_results = FLASHCARDS_RESULTS
            )
        else:
            # Si pas de sujet, utiliser tout le contenu du cours
            # On récupère tous les chunks du cours via ChromaDB
            from courses.vector_store import get_chroma_client
            collection = get_chroma_client().get_or_create_collection(f"course_{course.id}")
            results = collection.get()
            chunks = results.get('documents', [])[:FLASHCARDS_RESULTS] if results.get('documents') else []

        if not chunks:
            return Response(
                {"error": "Aucun contenu trouvé dans ce cours."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 4. Crée le deck vide IMMÉDIATEMENT en base
        deck_title = f"Fiches — {topic}" if topic else f"Fiches — {course.title}"
        deck = FlashcardDeck.objects.create(
            course = course,
            title  = deck_title,
            topic  = topic or '',  # Vide si pas de sujet
            status = FlashcardDeck.Status.PENDING   # ← statut initial
        )

        # 5. Lance la génération en arrière-plan via Celery
        generate_flashcards_task.delay(
            deck_id   = deck.id,
            chunks    = chunks,
            topic     = data.get('topic', ''),
            num_cards = data['num_cards']
        )

        # 6. Répond IMMÉDIATEMENT sans attendre Gemini
        return Response(
            FlashcardDeckSerializer(deck).data,
            status=status.HTTP_202_ACCEPTED   # 202 = "Accepté, traitement en cours"
        )


class DeckListView(generics.ListAPIView):
    """
    GET /api/flashcards/
    Liste tous les decks de l'utilisateur connecté
    """
    serializer_class   = FlashcardDeckSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class   = LargePagination

    def get_queryset(self):
        return FlashcardDeck.objects.filter(
            course__owner=self.request.user
        ).prefetch_related('flashcards')


class DeckDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/flashcards/<id>/   → détail d'un deck (utilisé pour le polling)
    PATCH  /api/flashcards/<id>/   → mise à jour partielle du statut ou des métadonnées
    DELETE /api/flashcards/<id>/   → supprimer un deck
    """
    serializer_class   = FlashcardDeckSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FlashcardDeck.objects.filter(
            course__owner=self.request.user
        ).prefetch_related('flashcards')


class UpdateMasteryView(APIView):
    """
    PATCH /api/flashcards/card/<id>/mastery/
    Met à jour le niveau de maîtrise d'une fiche
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        card = get_object_or_404(
            Flashcard,
            pk=pk,
            deck__course__owner=request.user
        )

        serializer = UpdateMasterySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        card.mastery = serializer.validated_data['mastery']
        card.save(update_fields=['mastery'])

        return Response(
            FlashcardSerializer(card).data,
            status=status.HTTP_200_OK
        )

"""
## Ce qui a changé vs l'ancien fichier
```
Avant :
→ Gemini générait les fiches dans la vue
→ L'utilisateur attendait 60s bloqué

Après :
→ Deck créé en base immédiatement (status: pending)
→ generate_flashcards_task.delay() lance Celery
→ Réponse en 50ms avec status 202 ✅
→ Celery génère en arrière-plan"""