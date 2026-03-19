# courses/tasks.py  ← nouveau fichier

from celery import shared_task
from .models import Course, CourseChunk
from .services import extract_text_from_pdf, extract_text_from_image, chunk_text
from .vector_store import store_chunks_embeddings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, queue='courses')
def process_course(self, course_id: int):
    """
    Tâche Celery déclenchée après chaque upload.
    Enchaîne : Extraction → Chunking → Embeddings → ChromaDB
    """
    try:
        course = Course.objects.get(id=course_id)

        # ── 1. Statut : en cours de traitement ──────────
        course.status = Course.Status.PROCESSING
        course.save(update_fields=['status'])
        logger.info(f"Traitement du cours {course_id} démarré")

        # ── 2. Extraction du texte ───────────────────────
        file_path = course.file.path   # chemin absolu sur le disque

        if course.file_type == 'pdf':
            pages = extract_text_from_pdf(file_path)
        else:
            pages = extract_text_from_image(file_path)

        logger.info(f"Cours {course_id} : {len(pages)} page(s) extraite(s)")

        # ── 3. Chunking ──────────────────────────────────
        chunks = chunk_text(pages, chunk_size=500, overlap=50)
        logger.info(f"Cours {course_id} : {len(chunks)} chunk(s) créé(s)")

        # ── 4. Sauvegarde des chunks en base ─────────────
        CourseChunk.objects.filter(course=course).delete()  # reset si retraitement
        CourseChunk.objects.bulk_create([
            CourseChunk(
                course      = course,
                content     = chunk["content"],
                page_number = chunk["page"],
                chunk_index = chunk["chunk_index"]
            )
            for chunk in chunks
        ])

        # ── 5. Embeddings + stockage ChromaDB ────────────
        store_chunks_embeddings(course_id, chunks)
        logger.info(f"Cours {course_id} : embeddings stockés dans ChromaDB")

        # ── 6. Statut final : prêt ───────────────────────
        course.status = Course.Status.READY
        course.save(update_fields=['status'])
        logger.info(f"✅ Cours {course_id} prêt !")

        return {"status": "success", "chunks": len(chunks)}

    except Course.DoesNotExist:
        logger.error(f"Cours {course_id} introuvable")
        return {"status": "error", "message": "Cours introuvable"}

    except Exception as exc:
        logger.error(f"Erreur traitement cours {course_id} : {exc}")
        # Met à jour le statut à "failed"
        Course.objects.filter(id=course_id).update(status=Course.Status.FAILED)
        # Celery réessaie jusqu'à 3 fois
        raise self.retry(exc=exc, countdown=30)