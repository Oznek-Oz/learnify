from django.urls import path

from .views import (
    LevelDetailView,
    LevelListView,
    LevelQuestionsView,
    ProgressView,
    StartLevelView,
    SubmitLevelView,
)

urlpatterns = [
    path('progress/', ProgressView.as_view(), name='quiz-game-progress'),
    path('levels/', LevelListView.as_view(), name='quiz-game-level-list'),
    path('levels/<int:number>/', LevelDetailView.as_view(), name='quiz-game-level-detail'),
    path('levels/<int:number>/questions/', LevelQuestionsView.as_view(), name='quiz-game-level-questions'),
    path('levels/<int:number>/start/', StartLevelView.as_view(), name='quiz-game-level-start'),
    path('levels/<int:number>/submit/', SubmitLevelView.as_view(), name='quiz-game-level-submit'),
]
