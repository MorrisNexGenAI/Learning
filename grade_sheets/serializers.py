from rest_framework import serializers
from .models import StudentGradeSheetPDF, LevelGradeSheetPDF

class StudentGradeSheetSerializer(serializers.ModelSerializer):
    view_url = serializers.ReadOnlyField()

    class Meta:
        model = StudentGradeSheetPDF
        fields = ['id', 'student', 'level', 'academic_year', 'filename', 'view_url', 'created_at', 'updated_at']

class LevelGradeSheetSerializer(serializers.ModelSerializer):
    view_url = serializers.ReadOnlyField()

    class Meta:
        model = LevelGradeSheetPDF
        fields = ['id', 'level', 'academic_year', 'filename', 'view_url', 'created_at', 'updated_at']