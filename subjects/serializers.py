from rest_framework import serializers
from .models import Subject
from levels.models import Level

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'subject', 'level', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_level(self, value):
        if not Level.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Invalid level ID")
        return value

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['level_id'] = instance.level.id  # Include level_id for frontend
        return representation