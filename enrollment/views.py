from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import Enrollment
from .serializers import EnrollmentSerializer
from .utils import edit_student
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

    @action(detail=False, methods=['POST'], url_path='edit', url_name='edit-student')
    def edit_student(self, request):
        """POST /api/enrollment/edit/ - Update or delete student details."""
        student_id = request.data.get('student_id')
        level_id = request.data.get('level_id')
        academic_year = request.data.get('academic_year')
        firstName = request.data.get('firstName')
        lastName = request.data.get('lastName')
        gender = request.data.get('gender')
        delete = request.data.get('delete', False)
        dob = request.data.get('dob')

        try:
            result = edit_student(student_id, level_id, academic_year, firstName, lastName, gender, dob, delete)
            return Response(result['response'], status=result['status'])
        except Exception as e:
            logger.error(f"Error in edit_student: {str(e)}")
            return Response({"error": f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)