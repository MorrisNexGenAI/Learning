from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from periods.models import Period
from periods.serializers import PeriodSerializer

class PeriodViewSet(viewsets.ModelViewSet):
    queryset = Period.objects.all()
    serializer_class = PeriodSerializer

def get_all_periods():
    """Fetch all periods."""
    return Period.objects.all()