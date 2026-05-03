# flashcards/serializers.py

from rest_framework import serializers
from config.app_config import FLASHCARDS_DEFAULT_CARDS, FLASHCARDS_MAX_CARDS, FLASHCARDS_MIN_CARDS
from .models import FlashcardDeck, Flashcard


class FlashcardSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Flashcard
        fields = [
            'id', 'front', 'back', 'hint',
            'mastery', 'order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class FlashcardDeckSerializer(serializers.ModelSerializer):
    flashcards   = FlashcardSerializer(many=True, read_only=True)
    course_title = serializers.ReadOnlyField(source='course.title')
    total_cards  = serializers.SerializerMethodField()

    class Meta:
        model  = FlashcardDeck
        fields = [
            'id', 'title', 'topic', 'status','course_title',
            'total_cards', 'flashcards', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_total_cards(self, obj):
        return obj.flashcards.count()


class GenerateFlashcardsSerializer(serializers.Serializer):
    """Validation des inputs pour la génération."""
    course_id = serializers.IntegerField()
    topic = serializers.CharField(max_length=255, required=False, allow_blank=True)
    num_cards = serializers.IntegerField(
        min_value=FLASHCARDS_MIN_CARDS,
        max_value=FLASHCARDS_MAX_CARDS,
        default=FLASHCARDS_DEFAULT_CARDS
    )


class UpdateMasterySerializer(serializers.Serializer):
    """Pour mettre à jour le niveau de maîtrise d'une fiche."""
    mastery = serializers.ChoiceField(
        choices=['new', 'learning', 'reviewing', 'mastered']
    )