from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from .models import Student
from .serializers import StudentSerializer
import logging

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        level_id = self.request.query_params.get('level_id')
        academic_year_id = self.request.query_params.get('academic_year_id')
        search = self.request.query_params.get('search')

        if level_id:
            queryset = queryset.filter(enrollment__level_id=level_id).distinct()
        if academic_year_id:
            queryset = queryset.filter(enrollment__academic_year_id=academic_year_id).distinct()
        if search:
            queryset = queryset.filter(
                models.Q(firstName__icontains=search) | models.Q(lastName__icontains=search)
            )

        return queryset.order_by('id')