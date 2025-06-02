from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from rest_framework.response import Response
from levels.models import Level
from levels.serializers import LevelSerializer

class LevelViewSet(viewsets.ModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer

def get_level_by_id(level_id):
    """Fetch a level by ID."""
    try:
        return Level.objects.get(id=level_id)
    except Level.DoesNotExist:
        return None

def get_all_levels():
    """Fetch all levels."""
    return Level.objects.all()