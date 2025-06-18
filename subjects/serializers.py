from rest_framework import serializers
from .models import Subject
from levels.serializers import LevelSerializer

class SubjectSerializer(serializers.ModelSerializer):
    level = LevelSerializer(read_only=True)

    class Meta:
        model = Subject
        fields = ['id', 'subject', 'level', 'updated_at']
        read_only_fields = ['id', 'updated_at']