from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from .models import AcademicYear
from .serializers import AcademicYearSerializer
import logging
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.all().order_by('-start_date')
    serializer_class = AcademicYearSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        cache_key = 'academic_years_queryset'
        queryset = cache.get(cache_key)
        if queryset is None:
            queryset = super().get_queryset()
            is_active = self.request.query_params.get('is_active')
            name = self.request.query_params.get('name')
            if is_active == 'true':
                today = timezone.now().date()
                queryset = queryset.filter(start_date__lte=today, end_date__gte=today)
            if name:
                queryset = queryset.filter(name__icontains=name)
            cache.set(cache_key, queryset, timeout=3600)  # Cache for 1 hour
        return queryset