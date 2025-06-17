import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Student
from .serializers import StudentSerializer
from levels.models import Level
from academic_years.models import AcademicYear

from .helper import (
    create_enrollment_for_student,
    create_pass_failed_status,
)

logger = logging.getLogger(__name__)

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            student = serializer.save()
            logger.info(f"Created student: {student.id} - {student.firstName} {student.lastName}")

            level_id = request.data.get('level')
            academic_year_id = request.data.get('academic_year')

            if not level_id or not academic_year_id:
                return Response({
                    "student": serializer.data,
                    "warning": "Student created but not enrolled due to missing level or academic_year"
                }, status=status.HTTP_201_CREATED)

            try:
                level = Level.objects.get(id=level_id)
                academic_year = AcademicYear.objects.get(id=academic_year_id)

                enrollment = create_enrollment_for_student(student, level, academic_year)
                create_pass_failed_status(student, level, academic_year, enrollment)

            except Exception as e:
                logger.error(f"Post-creation error: {str(e)}")
                return Response({
                    "student": serializer.data,
                    "error": f"Created but enrollment/pass_failed failed: {str(e)}"
                }, status=status.HTTP_201_CREATED)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating student: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        queryset = Student.objects.all()
        level_id = self.request.query_params.get('level_id')
        academic_year_name = self.request.query_params.get('academic_year')

        if level_id and academic_year_name:
            try:
                level = Level.objects.get(id=level_id)
                academic_year = AcademicYear.objects.get(name=academic_year_name)
                queryset = queryset.filter(
                    enrollment__level=level,
                    enrollment__academic_year=academic_year
                )
            except (Level.DoesNotExist, AcademicYear.DoesNotExist):
                return Student.objects.none()

        return queryset
