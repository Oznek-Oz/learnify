# users/urls.py

# On crée des URLs pour les endpoints liés aux utilisateurs (ex: inscription, login, profil, etc.) en utilisant les vues que nous avons créées dans users/views.py et les vues fournies par rest_framework_simplejwt pour gérer l'authentification avec JWT. Ces URLs seront incluses dans le fichier de configuration des URLs racines du projet (config/urls.py) pour être accessibles via l'API.

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,   # Login → retourne access + refresh token
    TokenRefreshView,      # Renouvelle l'access token
    TokenBlacklistView,    # Logout → invalide le refresh token
)
from .views import RegisterView, UserProfileView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/',    TokenObtainPairView.as_view(), name='login'),
    path('refresh/',  TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/',   TokenBlacklistView.as_view(), name='logout'),
    path('profile/',  UserProfileView.as_view(), name='profile'),
]