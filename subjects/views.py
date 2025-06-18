from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from .models import Subject
from .serializers import SubjectSerializer
import logging

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all().order_by('subject')
    serializer_class = SubjectSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        level_id = self.request.query_params.get('level_id')
        search = self.request.query_params.get('search')
        if level_id:
            queryset = queryset.filter(level_id=level_id)
        if search:
            queryset = queryset.filter(subject__icontains=search)
        return queryset.select_related('level')