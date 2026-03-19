# users/views.py

# On crée des vues pour gérer les endpoints de notre API liés aux utilisateurs (ex: inscription, profil, etc.) en utilisant les vues génériques de DRF (ex: CreateAPIView, RetrieveUpdateAPIView) pour simplifier la création de ces endpoints. On utilise des permissions (ex: AllowAny, IsAuthenticated) pour contrôler l'accès à ces endpoints en fonction de l'état d'authentification de l'utilisateur (ex: tout le monde peut s'inscrire, mais seul l'utilisateur connecté peut voir ou modifier son profil). On utilise également les serializers que nous avons créés dans users/serializers.py pour valider les données entrantes et formater les réponses JSON de nos endpoints.

from rest_framework import generics, permissions
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserProfileSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Accessible à tous (même non connecté)
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]  # ← pas besoin pour l'utilisateur d'être connecté


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET/PUT /api/auth/profile/
    Retourne le profil de l'utilisateur connecté
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user  # retourne l'utilisateur du token JWT