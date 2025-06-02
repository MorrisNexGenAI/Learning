from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .models import AcademicYear
from .serializers import AcademicYearSerializer

class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer