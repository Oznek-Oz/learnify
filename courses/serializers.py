from rest_framework import serializers
from config.app_config import COURSE_ALLOWED_EXTENSIONS, COURSE_MAX_FILE_SIZE_MB
from .models import Course


class CourseSerializer(serializers.ModelSerializer):

    owner_email = serializers.ReadOnlyField(source='owner.email')

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'file',
            'file_type', 'status', 'owner_email',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_type', 'status', 'owner_email',
            'created_at', 'updated_at'
        ]

    def validate_file(self, file):
        ext = file.name.rsplit('.', 1)[-1].lower()
        if ext not in COURSE_ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Format non supporté. Acceptés : {', '.join(COURSE_ALLOWED_EXTENSIONS)}"
            )

        if file.size > COURSE_MAX_FILE_SIZE_MB * 1024 * 1024:
            raise serializers.ValidationError(
                f"Fichier trop volumineux. Maximum : {COURSE_MAX_FILE_SIZE_MB} Mo."
            )

        return file

    def create(self, validated_data):
        file = validated_data['file']
        ext = file.name.rsplit('.', 1)[-1].lower()
        validated_data['file_type'] = 'pdf' if ext == 'pdf' else 'image'
        return super().create(validated_data)
