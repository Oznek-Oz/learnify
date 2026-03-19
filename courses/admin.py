# courses/admin.py

from django.contrib import admin
from .models import Course, CourseChunk


@admin.register(Course) # Enregistre le modèle Course dans l'admin de Django pour pouvoir gérer les cours via l'interface d'administration
class CourseAdmin(admin.ModelAdmin): # Personnalise l'affichage du modèle Course dans l'admin en définissant les champs à afficher, les filtres, les champs de recherche, etc.
    list_display  = ['title', 'owner', 'file_type', 'status', 'created_at']
    list_filter   = ['status', 'file_type']
    search_fields = ['title', 'owner__email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at'] # Affiche les cours les plus récents en premier dans l'admin


@admin.register(CourseChunk)
class CourseChunkAdmin(admin.ModelAdmin):
    list_display  = ['course', 'chunk_index', 'page_number', 'created_at']
    list_filter   = ['course']
    search_fields = ['content', 'course__title']