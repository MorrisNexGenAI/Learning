import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Grade
from .serializers import GradeSerializer
from .helper import get_grade_map, save_grade
from rest_framework.pagination import PageNumberPagination

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        student_id = self.request.query_params.get('student_id')
        subject_id = self.request.query_params.get('subject_id')
        period_id = self.request.query_params.get('period_id')
        academic_year_id = self.request.query_params.get('academic_year_id')

        if student_id:
            queryset = queryset.filter(enrollment__student_id=student_id)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if period_id:
            queryset = queryset.filter(period_id=period_id)
        if academic_year_id:
            queryset = queryset.filter(enrollment__academic_year_id=academic_year_id)

        return queryset.select_related('enrollment__student', 'subject', 'period')

    def create(self, request, *args, **kwargs):
        if isinstance(request.data, list):
            serializer = self.get_serializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return super().create(request, *args, **kwargs)