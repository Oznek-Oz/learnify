from rest_framework import serializers

from courses.models import Course
from .models import Level, LevelProgress, QuizGameProgress, GameQuestion


class GameQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameQuestion
        fields = [
            'id', 'question_text', 'option_a', 'option_b',
            'option_c', 'option_d', 'correct_answer', 'explanation', 'order'
        ]


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ['id', 'number', 'title', 'difficulty', 'quiz_count', 'description', 'is_active']


class LevelProgressSerializer(serializers.ModelSerializer):
    level = LevelSerializer(read_only=True)

    class Meta:
        model = LevelProgress
        fields = [
            'id', 'level', 'status', 'completed_quiz_count',
            'required_quiz_count', 'generated_questions', 'score', 'unlocked_at', 'completed_at'
        ]
        read_only_fields = ['id', 'level', 'unlocked_at', 'completed_at', 'generated_questions']


class QuizGameProgressSerializer(serializers.ModelSerializer):
    course_title = serializers.ReadOnlyField(source='course.title')
    unlocked_levels = LevelSerializer(many=True, read_only=True)
    completed_levels = LevelSerializer(many=True, read_only=True)
    level_progresses = LevelProgressSerializer(many=True, read_only=True)

    class Meta:
        model = QuizGameProgress
        fields = [
            'id', 'course', 'course_title', 'topic',
            'unlocked_levels', 'completed_levels', 'level_progresses',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CreateProgressSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    topic = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_course_id(self, value):
        if not Course.objects.filter(id=value).exists():
            raise serializers.ValidationError("Le cours n'existe pas.")
        return value


class SubmitLevelSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    topic = serializers.CharField(max_length=255, required=False, allow_blank=True)
    completed_quiz_count = serializers.IntegerField(min_value=0)
    score = serializers.DecimalField(max_digits=5, decimal_places=2)
    passed = serializers.BooleanField(default=True)

    def validate_course_id(self, value):
        if not Course.objects.filter(id=value).exists():
            raise serializers.ValidationError("Le cours n'existe pas.")
        return value


class StartLevelSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    topic = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_course_id(self, value):
        if not Course.objects.filter(id=value).exists():
            raise serializers.ValidationError("Le cours n'existe pas.")
        return value
