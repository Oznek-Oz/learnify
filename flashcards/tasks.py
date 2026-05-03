# flashcards/tasks.py ← nouveau fichier

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from .models import FlashcardDeck, Flashcard
from .gemini_service import generate_flashcards_from_chunks_safe
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    time_limit=300,        # Max 5 minutes total
    soft_time_limit=270,   # Alerte à 4.5 minutes
    default_retry_delay=30,
    queue='generation'
)
def generate_flashcards_task(self, deck_id, chunks, topic, num_cards):
    try:
        deck        = FlashcardDeck.objects.get(id=deck_id)
        deck.status = FlashcardDeck.Status.GENERATING
        deck.save(update_fields=['status'])

        cards_data = generate_flashcards_from_chunks_safe(
            chunks    = chunks,
            topic     = topic,
            num_cards = num_cards
        )

        Flashcard.objects.bulk_create([
            Flashcard(
                deck  = deck,
                front = card['front'],
                back  = card['back'],
                hint  = card.get('hint', ''),
                order = i
            )
            for i, card in enumerate(cards_data, start=1)
        ])

        deck.status = FlashcardDeck.Status.READY
        deck.save(update_fields=['status'])
        logger.info(f"✅ Deck {deck_id} prêt — {len(cards_data)} fiches")

    except SoftTimeLimitExceeded:
        logger.error(f"Timeout génération deck {deck_id}")
        FlashcardDeck.objects.filter(id=deck_id).update(
            status=FlashcardDeck.Status.FAILED
        )
        return {"status": "error", "message": "Timeout - génération trop longue"}

    except FlashcardDeck.DoesNotExist:
        logger.error(f"Deck {deck_id} introuvable")

    except Exception as exc:
        FlashcardDeck.objects.filter(id=deck_id).update(
            status=FlashcardDeck.Status.FAILED
        )
        logger.error(f"Erreur deck {deck_id} : {exc}")
        raise self.retry(exc=exc)