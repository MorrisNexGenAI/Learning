from rest_framework import serializers
from .models import PassFailedStatus

class PassFailedStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassFailedStatus
        fields = ['id', 'student', 'level', 'academic_year', 'enrollment', 'status', 'validated_at', 'validated_by', 'template_name']