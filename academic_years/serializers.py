from rest_framework import serializers
from .models import AcademicYear

class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ['id', 'name', 'start_date', 'end_date']
        read_only_fields = ['id']