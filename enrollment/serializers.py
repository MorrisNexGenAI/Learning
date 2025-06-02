from rest_framework import serializers
from .models import Enrollment
from students.serializers import StudentSerializer
from levels.serializers import LevelSerializer
from academic_years.serializers import AcademicYearSerializer  # Adjust path

class EnrollmentSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    level = LevelSerializer(read_only=True)
    academic_year = AcademicYearSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'level', 'academic_year', 'date_enrolled']