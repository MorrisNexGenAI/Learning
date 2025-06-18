from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from .models import Level
from .serializers import LevelSerializer
import logging

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

class LevelViewSet(viewsets.ModelViewSet):
    queryset = Level.objects.all().order_by('name')
    serializer_class = LevelSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset