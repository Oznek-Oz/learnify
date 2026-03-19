# users/serializers.py

# On crée des serializers pour convertir les instances de nos modèles (ex: User) en formats JSON ou autres, et pour valider les données entrantes lors de la création ou mise à jour d'instances (ex: lors de l'inscription d'un nouvel utilisateur)
# On utilise les serializers de DRF pour faciliter la création d'API RESTful et gérer l'authentification avec JWT (JSON Web Tokens) pour sécuriser les endpoints de notre API.
# On crée un serializer pour l'inscription des utilisateurs (RegisterSerializer) qui valide les données d'entrée (ex: mot de passe, email) et crée une nouvelle instance de User, et un serializer pour afficher les profils des utilisateurs (UserProfileSerializer) qui retourne les champs pertinents (ex: id, username, email, date_joined) sans exposer les informations sensibles (ex: mot de passe).

from rest_framework import serializers # On importe les serializers de DRF pour pouvoir créer des serializers pour nos modèles (ex: User)
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField( # On définit un champ de mot de passe qui est write_only (il ne sera pas retourné dans les réponses) et qui utilise les validateurs de mot de passe de Django pour assurer la sécurité des mots de passe choisis par les utilisateurs
        write_only=True,        # le mot de passe ne revient jamais dans la réponse
        required=True,
        validators=[validate_password] 
    )
    password2 = serializers.CharField(write_only=True, required=True) # On ajoute un champ de confirmation de mot de passe (password2) pour s'assurer que l'utilisateur a bien saisi le même mot de passe deux fois lors de l'inscription, ce qui est une pratique courante pour éviter les erreurs de saisie.

    # On spécifie que ce serializer est basé sur le modèle User et que les champs à inclure sont username, email, password et password2. Le champ password2 est utilisé uniquement pour la validation et ne sera pas stocké dans la base de données.
    class Meta: 
        model = User
        fields = ('username', 'email', 'password', 'password2')

    # On ajoute une méthode de validation personnalisée pour vérifier que les deux champs de mot de passe (password et password2) correspondent. Si les mots de passe ne correspondent pas, une ValidationError est levée avec un message d'erreur approprié.
    def validate(self, attrs): 
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Les mots de passe ne correspondent pas."}
            )
        return attrs

    # On ajoute une méthode create personnalisée pour créer une nouvelle instance de User en utilisant la méthode create_user fournie par le modèle User de Django, qui gère correctement le hachage du mot de passe et les autres champs nécessaires. Avant de créer l'utilisateur, on supprime le champ password2 des données validées car il n'est pas nécessaire pour la création de l'utilisateur.
    def create(self, validated_data):
        validated_data.pop('password2') #
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'date_joined')
        read_only_fields = ('id', 'date_joined')