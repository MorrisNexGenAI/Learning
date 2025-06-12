from rest_framework import serializers
from .models import PassFailedStatus
from students.serializers import StudentSerializer
from levels.serializers import LevelSerializer
from academic_years.serializers import AcademicYearSerializer
from enrollment.serializers import EnrollmentSerializer

class PassFailedStatusSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    level = LevelSerializer(read_only=True)
    academic_year = AcademicYearSerializer(read_only=True)
    enrollment = EnrollmentSerializer(read_only=True, allow_null=True)

    class Meta:
        model = PassFailedStatus
        fields = ['id', 'student', 'level', 'academic_year', 'enrollment', 'status',
                  'validated_at', 'validated_by', 'template_name', 'grades_complete']
