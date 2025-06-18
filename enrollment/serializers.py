from rest_framework import serializers
from .models import Enrollment
from students.models import Student
from levels.models import Level
from academic_years.models import AcademicYear

class EnrollmentSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all())
    level = serializers.PrimaryKeyRelatedField(queryset=Level.objects.all())
    academic_year = serializers.PrimaryKeyRelatedField(queryset=AcademicYear.objects.all())

    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'level', 'academic_year', 'date_enrolled', 'enrollment_status']

