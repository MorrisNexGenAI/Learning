from rest_framework import serializers
from .models import Grade
from enrollment.models import Enrollment

class GradeSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(source='enrollment.student.id', read_only=True)
    student_name = serializers.CharField(source='enrollment.student', read_only=True)
    score = serializers.IntegerField(min_value=0, max_value=100)

    class Meta:
        model = Grade
        fields = ['id', 'student_id', 'student_name', 'score', 'enrollment', 'subject', 'period']
        read_only_fields = ['id', 'student_id', 'student_name']

    def validate_score(self, value):
        if not isinstance(value, int):
            raise serializers.ValidationError("Score must be an integer between 0 and 100.")
        return value