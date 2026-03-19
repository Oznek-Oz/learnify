# quizz/tasks.py ← nouveau fichier

from celery import shared_task
from .models import Quiz, Question
from .gemini_service import generate_quiz_from_chunks
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10, queue='generation')
def generate_quiz_task(self, quiz_id, chunks, topic, difficulty, num_questions):
    try:
        quiz        = Quiz.objects.get(id=quiz_id)
        quiz.status = Quiz.Status.GENERATING
        quiz.save(update_fields=['status'])

        questions_data = generate_quiz_from_chunks(
            chunks        = chunks,
            topic         = topic,
            difficulty    = difficulty,
            num_questions = num_questions
        )

        Question.objects.bulk_create([
            Question(
                quiz           = quiz,
                question_text  = q['question'],
                option_a       = q['option_a'],
                option_b       = q['option_b'],
                option_c       = q['option_c'],
                option_d       = q['option_d'],
                correct_answer = q['correct_answer'].upper(),
                explanation    = q.get('explanation', ''),
                order          = i
            )
            for i, q in enumerate(questions_data, start=1)
        ])

        quiz.status = Quiz.Status.READY
        quiz.save(update_fields=['status'])
        logger.info(f"✅ Quiz {quiz_id} prêt — {len(questions_data)} questions")

    except Quiz.DoesNotExist:
        logger.error(f"Quiz {quiz_id} introuvable")

    except Exception as exc:
        Quiz.objects.filter(id=quiz_id).update(status=Quiz.Status.FAILED)
        logger.error(f"Erreur quiz {quiz_id} : {exc}")
        raise self.retry(exc=exc)