# courses/serializers.py

from rest_framework import serializers
from .models import Course

ALLOWED_EXTENSIONS = ['pdf', 'docx', 'png', 'jpg', 'jpeg', 'webp']
MAX_FILE_SIZE_MB = 20  # 20 Mo maximum

class CourseSerializer(serializers.ModelSerializer):

    owner_email = serializers.ReadOnlyField(source='owner.email')

    class Meta:
        model  = Course
        fields = [
            'id', 'title', 'description', 'file',
            'file_type', 'status', 'owner_email',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'file_type', 'status', 'owner_email', 'created_at', 'updated_at']

    def validate_file(self, file):
        # 1. Vérifier l'extension
        ext = file.name.split('.')[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Format non supporté. Acceptés : {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # 2. Vérifier la taille
        if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise serializers.ValidationError(
                f"Fichier trop volumineux. Maximum : {MAX_FILE_SIZE_MB} Mo."
            )

        return file

    def create(self, validated_data):
        # Détecter automatiquement le type de fichier
        file = validated_data['file']
        ext  = file.name.split('.')[-1].lower()
        validated_data['file_type'] = 'pdf' if ext == 'pdf' else 'image'

        return # courses/serializers.py

from rest_framework import serializers
from .models import Course

ALLOWED_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg', 'webp']
MAX_FILE_SIZE_MB = 20  # 20 Mo maximum

class CourseSerializer(serializers.ModelSerializer):

    owner_email = serializers.ReadOnlyField(source='owner.email')

    class Meta:
        model  = Course
        fields = [
            'id', 'title', 'description', 'file',
            'file_type', 'status', 'owner_email',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'file_type', 'status', 'owner_email', 'created_at', 'updated_at']

    def validate_file(self, file):
        # 1. Vérifier l'extension
        ext = file.name.split('.')[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Format non supporté. Acceptés : {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # 2. Vérifier la taille
        if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise serializers.ValidationError(
                f"Fichier trop volumineux. Maximum : {MAX_FILE_SIZE_MB} Mo."
            )

        return file

    def create(self, validated_data):
        # Détecter automatiquement le type de fichier
        file = validated_data['file']
        ext  = file.name.split('.')[-1].lower()
        validated_data['file_type'] = 'pdf' if ext == 'pdf' else 'image'

        return super().create(validated_data)