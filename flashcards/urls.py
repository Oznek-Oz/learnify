# flashcards/urls.py

from django.urls import path
from .views import (
    GenerateFlashcardsView,
    DeckListView,
    DeckDetailView,
    UpdateMasteryView
)

urlpatterns = [
    path('',                         DeckListView.as_view(),        name='deck-list'),
    path('generate/',                GenerateFlashcardsView.as_view(), name='flashcards-generate'),
    path('<int:pk>/',                DeckDetailView.as_view(),      name='deck-detail'),
    path('card/<int:pk>/mastery/',   UpdateMasteryView.as_view(),   name='card-mastery'),
]