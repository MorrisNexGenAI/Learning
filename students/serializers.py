# students/serializers.py
from rest_framework import serializers
from students.models import Student
from levels.models import Level
from enrollment.models import Enrollment
from levels.serializers import LevelSerializer  # Use your provided serializer

class StudentSerializer(serializers.ModelSerializer):
    level = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ['id', 'firstName', 'lastName', 'gender', 'dob', 'level']

    def get_level(self, obj):
        # Derive level from the first enrollment using LevelSerializer
        enrollment = obj.enrollments.first()
        if enrollment:
            return LevelSerializer(enrollment.level).data
        return None

    def create(self, validated_data):
        # Remove level from validated_data since it's not a direct field
        validated_data.pop('level', None)
        student = Student.objects.create(**validated_data)
        return student  # Enrollment handled in ViewSet