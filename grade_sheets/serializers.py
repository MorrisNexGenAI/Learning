from rest_framework import serializers
from .models import GradeSheet

class GradeSheetserializer(serializers.ModelSerializer):
    class Meta:
        model = GradeSheet
        fields = '__all__'