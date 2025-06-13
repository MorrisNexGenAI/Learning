from rest_framework import serializers
from .models import GradeSheetPDF

class GradeSheetserializer(serializers.ModelSerializer):
    class Meta:
        model = GradeSheetPDF
        fields = '__all__'