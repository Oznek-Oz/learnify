# flashcards/admin.py

from django.contrib import admin
from .models import FlashcardDeck, Flashcard


class FlashcardInline(admin.TabularInline):
    model  = Flashcard
    extra  = 0
    fields = ['order', 'front', 'mastery']


@admin.register(FlashcardDeck)
class FlashcardDeckAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'created_at']
    inlines      = [FlashcardInline]


@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display  = ['order', 'front', 'deck', 'mastery']
    list_filter   = ['mastery']
    search_fields = ['front', 'back']