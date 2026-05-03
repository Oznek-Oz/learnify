# courses/tasks.py

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from .models import Course, CourseChunk
from .services import extract_text_from_pdf, extract_text_from_image, chunk_text_adaptive
from .vector_store import store_chunks_embeddings
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    time_limit=600,
    soft_time_limit=540,
    default_retry_delay=30,
    queue='courses'
)
def process_course(self, course_id: int):
    """
    Pipeline de traitement du cours :
    1. Extraction de texte / OCR
    2. Chunking adaptatif
    3. Génération d'embeddings et stockage ChromaDB
    """
    try:
        course = Course.objects.get(id=course_id)

        course.status = Course.Status.PROCESSING
        course.save(update_fields=['status'])
        logger.info(f"Traitement du cours {course_id} démarré")

        file_path = course.file.path
        if course.file_type == 'pdf':
            pages = extract_text_from_pdf(file_path)
        else:
            pages = extract_text_from_image(file_path)

        if not pages or not any(page.get('text', '').strip() for page in pages):
            logger.warning(f"Cours {course_id} : aucun texte extrait")
            course.status = Course.Status.FAILED
            course.save(update_fields=['status'])
            return {"status": "error", "message": "Aucun texte extrait du fichier."}

        logger.info(f"Cours {course_id} : {len(pages)} page(s) traitée(s)")

        chunks = chunk_text_adaptive(pages, file_type=course.file_type)
        logger.info(f"Cours {course_id} : {len(chunks)} chunk(s) créé(s)")

        if not chunks:
            logger.warning(f"Cours {course_id} : aucun chunk créé après chunking")
            course.status = Course.Status.FAILED
            course.save(update_fields=['status'])
            return {"status": "error", "message": "Aucun chunk créé."}

        CourseChunk.objects.filter(course=course).delete()
        CourseChunk.objects.bulk_create([
            CourseChunk(
                course=course,
                content=chunk["content"],
                page_number=chunk["page"],
                chunk_index=chunk["chunk_index"]
            )
            for chunk in chunks
        ])

        store_chunks_embeddings(course_id, chunks)
        logger.info(f"Cours {course_id} : embeddings stockés dans ChromaDB")

        course.status = Course.Status.READY
        course.save(update_fields=['status'])
        logger.info(f"Cours {course_id} prêt")

        return {"status": "success", "chunks": len(chunks)}

    except SoftTimeLimitExceeded:
        logger.error(f"Timeout traitement cours {course_id}")
        Course.objects.filter(id=course_id).update(status=Course.Status.FAILED)
        return {"status": "error", "message": "Timeout - traitement trop long"}

    except Course.DoesNotExist:
        logger.error(f"Cours {course_id} introuvable")
        return {"status": "error", "message": "Cours introuvable"}

    except Exception as exc:
        logger.exception(f"Erreur traitement cours {course_id}")
        Course.objects.filter(id=course_id).update(status=Course.Status.FAILED)
        raise self.retry(exc=exc, countdown=30)