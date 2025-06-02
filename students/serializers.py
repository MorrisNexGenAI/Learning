from rest_framework import serializers
from students.models import Student
from levels.models import Level
from enrollment.models import Enrollment
from levels.serializers import LevelSerializer
from academic_years.models import AcademicYear

class StudentSerializer(serializers.ModelSerializer):
    level = serializers.SerializerMethodField()
    academic_year = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ['id', 'firstName', 'lastName', 'gender', 'dob', 'level', 'academic_year']

    def get_level(self, obj):
        enrollment = obj.enrollments.first()
        if enrollment and enrollment.level:
            return LevelSerializer(enrollment.level).data
        return None

    def get_academic_year(self, obj):
        enrollment = obj.enrollments.first()
        if enrollment and enrollment.academic_year:
            return {'id': enrollment.academic_year.id, 'name': enrollment.academic_year.name}
        return None

    def create(self, validated_data):
        student = Student.objects.create(**validated_data)
        return student  # Enrollment will be handled in ViewSet