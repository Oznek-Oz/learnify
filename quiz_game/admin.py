from django.contrib import admin

from .models import Level, QuizGameProgress, LevelProgress


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('number', 'title', 'difficulty', 'quiz_count', 'is_active')
    list_filter = ('difficulty', 'is_active')
    ordering = ('number',)


@admin.register(QuizGameProgress)
class QuizGameProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'topic', 'created_at', 'updated_at')
    search_fields = ('user__email', 'course__title', 'topic')
    filter_horizontal = ('unlocked_levels', 'completed_levels')


@admin.register(LevelProgress)
class LevelProgressAdmin(admin.ModelAdmin):
    list_display = ('user_progress', 'level', 'status', 'completed_quiz_count', 'required_quiz_count')
    list_filter = ('status',)
    search_fields = ('user_progress__user__email', 'level__title')
