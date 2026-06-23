from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
import logging

from courses.vector_store import search_similar_chunks
from quizz.gemini_service import generate_quiz_from_chunks_safe
from config.app_config import QUIZ_SEARCH_RESULTS

from .models import QuizGameProgress, LevelProgress, GameQuestion

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    time_limit=300,
    soft_time_limit=270,
    default_retry_delay=30,
    queue='generation'
)
def generate_level_quizzes_task(self, user_progress_id, level_number, topic):
    """
    Génère les quiz pour un niveau donné en arrière-plan.
    Effectue une recherche RAG sur le cours pour récupérer des chunks pertinents.
    """
    try:
        progress = QuizGameProgress.objects.select_related('course').get(id=user_progress_id)
        level_progress = LevelProgress.objects.select_related('level', 'user_progress').get(
            user_progress=progress,
            level__number=level_number
        )

        # 1. Recherche des chunks pertinents du cours
        if topic:
            chunks = search_similar_chunks(
                course_id=progress.course.id,
                query=topic,
                n_results=QUIZ_SEARCH_RESULTS
            )
        else:
            # Si pas de topic, récupérer tous les chunks du cours depuis la base
            from courses.models import CourseChunk
            chunks_qs = CourseChunk.objects.filter(course=progress.course).order_by('chunk_index')[:QUIZ_SEARCH_RESULTS]
            chunks = [c.content for c in chunks_qs]

        if not chunks:
            logger.warning(f"Aucun chunk trouvé pour le niveau {level_number}, progression {user_progress_id}")
            level_progress.status = LevelProgress.Status.FAILED
            level_progress.save(update_fields=['status'])
            return

        # 2. Générer les questions via Gemini
        level = level_progress.level
        num_questions = level.quiz_count
        difficulty = level.difficulty

        questions_data = generate_quiz_from_chunks_safe(
            chunks=chunks,
            topic=topic or progress.course.title,
            difficulty=difficulty,
            num_questions=num_questions
        )

        # 3. Sauvegarder les questions générées
        GameQuestion.objects.bulk_create([
            GameQuestion(
                level_progress=level_progress,
                question_text=q['question'],
                option_a=q['option_a'],
                option_b=q['option_b'],
                option_c=q['option_c'],
                option_d=q['option_d'],
                correct_answer=q['correct_answer'].upper(),
                explanation=q.get('explanation', ''),
                order=i
            )
            for i, q in enumerate(questions_data, start=1)
        ])

        level_progress.generated_questions = len(questions_data)
        level_progress.status = LevelProgress.Status.READY
        level_progress.save()

        logger.info(f"✅ Niveau {level_number} prêt — {len(questions_data)} questions générées")

    except SoftTimeLimitExceeded:
        logger.error(f"Timeout génération niveau {level_number}, progression {user_progress_id}")
        try:
            progress = QuizGameProgress.objects.get(id=user_progress_id)
            LevelProgress.objects.filter(user_progress=progress, level__number=level_number).update(
                status=LevelProgress.Status.FAILED
            )
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut : {e}")
        return {"status": "error", "message": "Timeout"}

    except QuizGameProgress.DoesNotExist:
        logger.error(f"Progression {user_progress_id} introuvable")

    except Exception as exc:
        logger.error(f"Erreur génération niveau {level_number} : {exc}")
        try:
            progress = QuizGameProgress.objects.get(id=user_progress_id)
            LevelProgress.objects.filter(user_progress=progress, level__number=level_number).update(
                status=LevelProgress.Status.FAILED
            )
        except:
            pass
        raise self.retry(exc=exc)
