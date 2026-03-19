# quiz/urls.py

from django.urls import path
from .views import GenerateQuizView, QuizListView, QuizDetailView

urlpatterns = [
    path('',            QuizListView.as_view(),    name='quiz-list'),
    path('generate/',   GenerateQuizView.as_view(), name='quiz-generate'),
    path('<int:pk>/',   QuizDetailView.as_view(),   name='quiz-detail'),
]