# courses/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle

from config.throttles import CourseUploadThrottle
from courses.tasks import process_course
from .models import Course
from .serializers import CourseSerializer


class CourseListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/courses/       → liste des cours de l'utilisateur connecté
    POST /api/courses/       → uploader un nouveau cours
    """
    serializer_class   = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes  = [CourseUploadThrottle]

    def get_throttles(self):
        # Applique le throttle d'upload strict seulement au POST
        # GET utilise le throttle par défaut (user: 1000/day)
        if self.request.method == 'POST':
            return [CourseUploadThrottle()]
        return [UserRateThrottle()]

    def get_queryset(self):
        # Chaque user ne voit QUE ses propres cours
        return Course.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        # L'owner est automatiquement l'utilisateur connecté
        course = serializer.save(owner=self.request.user)
        
        # Lance le traitement en arrière-plan juste après l'upload
        process_course.delay(course.id)   # .delay() = asynchrone ✅


class CourseDetailView(generics.RetrieveDestroyAPIView):
    """
    GET    /api/courses/<id>/   → détail d'un cours
    DELETE /api/courses/<id>/   → supprimer un cours
    """
    serializer_class   = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Un user ne peut accéder qu'à SES cours
        return Course.objects.filter(owner=self.request.user)
    

