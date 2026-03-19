# users/models.py

from django.contrib.auth.models import AbstractUser # On importe AbstractUser pour pouvoir étendre le modèle utilisateur de Django et ajouter nos propres champs (ex: email, avatar, etc.)
from django.db import models

class CustomUser(AbstractUser):
    """
    On étend le modèle User de Django pour ajouter
    nos propres champs plus tard (avatar, niveau, etc.)
    """
    email = models.EmailField(unique=True)

    # On veut que l'email soit le champ de connexion
    # (pas le username)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email # Affiche l'email de l'utilisateur dans l'admin et les templates au lieu du username