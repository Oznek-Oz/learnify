from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Course
from .models import Level, LevelProgress, QuizGameProgress, GameQuestion
from .serializers import (
    CreateProgressSerializer,
    GameQuestionSerializer,
    LevelProgressSerializer,
    LevelSerializer,
    QuizGameProgressSerializer,
    StartLevelSerializer,
    SubmitLevelSerializer,
)


class ProgressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = CreateProgressSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        course = get_object_or_404(
            Course,
            id=serializer.validated_data['course_id'],
            owner=request.user
        )
        topic = serializer.validated_data.get('topic', '').strip()
        progress, _ = QuizGameProgress.objects.get_or_create(
            user=request.user,
            course=course,
            topic=topic,
        )
        progress.ensure_initialized()
        progress.save()
        return Response(QuizGameProgressSerializer(progress).data)

    def post(self, request):
        serializer = CreateProgressSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        course = get_object_or_404(
            Course,
            id=serializer.validated_data['course_id'],
            owner=request.user
        )
        topic = serializer.validated_data.get('topic', '').strip()
        progress, created = QuizGameProgress.objects.get_or_create(
            user=request.user,
            course=course,
            topic=topic,
        )
        progress.ensure_initialized()
        progress.save()
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(QuizGameProgressSerializer(progress).data, status=status_code)


class LevelListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LevelSerializer
    queryset = Level.objects.filter(is_active=True)


class LevelDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LevelSerializer
    queryset = Level.objects.filter(is_active=True)
    lookup_field = 'number'
    lookup_url_kwarg = 'number'


class StartLevelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, number):
        serializer = StartLevelSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        course = get_object_or_404(
            Course,
            id=serializer.validated_data['course_id'],
            owner=request.user
        )
        topic = serializer.validated_data.get('topic', '').strip()
        progress, _ = QuizGameProgress.objects.get_or_create(
            user=request.user,
            course=course,
            topic=topic,
        )
        progress.ensure_initialized()
        progress.save()

        level = get_object_or_404(Level, number=number, is_active=True)
        if not progress.is_level_unlocked(level):
            return Response(
                {'detail': 'Niveau non débloqué ou déjà complété.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        level_progress, created = LevelProgress.objects.get_or_create(
            user_progress=progress,
            level=level,
            defaults={
                'required_quiz_count': level.quiz_count,
                'status': LevelProgress.Status.GENERATING,
                'unlocked_at': timezone.now(),
            }
        )
        
        # Si le niveau est encore en génération, on le note à l'utilisateur
        if level_progress.status == LevelProgress.Status.GENERATING:
            return Response(
                LevelProgressSerializer(level_progress).data,
                status=status.HTTP_202_ACCEPTED
            )
        
        # Sinon, on met en IN_PROGRESS
        if not created:
            level_progress.status = LevelProgress.Status.IN_PROGRESS
            level_progress.required_quiz_count = level.quiz_count
            level_progress.unlocked_at = level_progress.unlocked_at or timezone.now()
            level_progress.save()

        return Response(LevelProgressSerializer(level_progress).data)


class SubmitLevelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, number):
        serializer = SubmitLevelSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        course = get_object_or_404(
            Course,
            id=serializer.validated_data['course_id'],
            owner=request.user
        )
        topic = serializer.validated_data.get('topic', '').strip()
        progress = get_object_or_404(
            QuizGameProgress,
            user=request.user,
            course=course,
            topic=topic,
        )

        level = get_object_or_404(Level, number=number, is_active=True)
        if not progress.is_level_unlocked(level):
            return Response(
                {'detail': 'Niveau non débloqué ou déjà complété.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        level_progress, _ = LevelProgress.objects.get_or_create(
            user_progress=progress,
            level=level,
            defaults={'required_quiz_count': level.quiz_count}
        )
        level_progress.completed_quiz_count = serializer.validated_data['completed_quiz_count']
        level_progress.score = serializer.validated_data['score']
        if serializer.validated_data['passed']:
            level_progress.status = LevelProgress.Status.PASSED
            progress.complete_level(level)
        else:
            level_progress.status = LevelProgress.Status.FAILED
        level_progress.save()

        return Response(QuizGameProgressSerializer(progress).data)


class LevelQuestionsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameQuestionSerializer
    
    def get_queryset(self):
        user = self.request.user
        number = self.kwargs['number']
        
        level = get_object_or_404(Level, number=number, is_active=True)
        
        # Get course and topic from query params
        course_id = self.request.query_params.get('course_id')
        topic = self.request.query_params.get('topic', '')
        
        if not course_id:
            return GameQuestion.objects.none()
            
        course = get_object_or_404(Course, id=course_id, owner=user)
        
        # Get the progress
        progress = get_object_or_404(
            QuizGameProgress,
            user=user,
            course=course,
            topic=topic,
        )
        
        # Get the level progress
        level_progress = get_object_or_404(
            LevelProgress,
            user_progress=progress,
            level=level,
        )
        
        return level_progress.questions.all()
