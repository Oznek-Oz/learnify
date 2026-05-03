from rest_framework import serializers
from config.app_config import QUIZ_DEFAULT_QUESTIONS, QUIZ_MAX_QUESTIONS, QUIZ_MIN_QUESTIONS
from .models import Quiz, Question


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            'id', 'question_text',
            'option_a', 'option_b', 'option_c', 'option_d',
            'correct_answer', 'explanation', 'order'
        ]


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    course_title = serializers.ReadOnlyField(source='course.title')

    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'difficulty', 'topic', 'status',
            'course_title', 'questions', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class GenerateQuizSerializer(serializers.Serializer):
    """
    Serializer pour la requête de génération.
    Pas un ModelSerializer — juste une validation des inputs.
    """
    course_id = serializers.IntegerField()
    topic = serializers.CharField(max_length=255, required=False, allow_blank=True)
    difficulty = serializers.ChoiceField(
        choices=['easy', 'medium', 'hard'],
        default='medium'
    )
    num_questions = serializers.IntegerField(
        min_value=QUIZ_MIN_QUESTIONS,
        max_value=QUIZ_MAX_QUESTIONS,
        default=QUIZ_DEFAULT_QUESTIONS
    )
