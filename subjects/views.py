from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from subjects.models import Subject
from subjects.serializers import SubjectSerializer

class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubjectSerializer

    def get_queryset(self):
        queryset = Subject.objects.all()
        level_id = self.request.query_params.get('level_id')
        if level_id:
            queryset = queryset.filter(level_id=level_id)
        return queryset

def get_subjects_by_level(level_id):
    """Fetch subjects by level and return as a dictionary."""
    subjects = Subject.objects.filter(level_id=level_id)
    return {s.id: s.subject for s in subjects}