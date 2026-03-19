# quiz/admin.py

from django.contrib import admin
from .models import Quiz, Question

class QuestionInline(admin.TabularInline):
    model  = Question
    extra  = 0
    fields = ['order', 'question_text', 'correct_answer']

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'difficulty', 'created_at']
    list_filter  = ['difficulty']
    inlines      = [QuestionInline]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['order', 'question_text', 'quiz', 'correct_answer']