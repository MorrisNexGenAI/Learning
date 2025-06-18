from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from .models import Enrollment
from .serializers import EnrollmentSerializer
import logging

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        student_id = self.request.query_params.get('student_id')
        level_id = self.request.query_params.get('level_id')
        academic_year_id = self.request.query_params.get('academic_year_id')

        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if level_id:
            queryset = queryset.filter(level_id=level_id)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)

        return queryset
        