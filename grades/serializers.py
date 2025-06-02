# grades/serializers.py
from rest_framework import serializers
from grades.models import Grade

class GradeSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(source='enrollment.student.id', read_only=True)
    student_name = serializers.CharField(source='enrollment.student.__str__', read_only=True)
    score = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)

    def validate_score(self, value):
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Score must be between 0 and 100.")
        return value

    class Meta:
        model = Grade
        fields = ['student_id', 'student_name', 'score', 'enrollment', 'subject', 'period']