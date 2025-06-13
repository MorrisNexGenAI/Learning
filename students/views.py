import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Student
from .serializers import StudentSerializer
from enrollment.models import Enrollment
from academic_years.models import AcademicYear
from levels.models import Level
from pass_and_failed.models import PassFailedStatus
from grades.models import Grade
from subjects.models import Subject

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

            # Extract level and academic_year from request data
            level_id = request.data.get('level')
            academic_year_id = request.data.get('academic_year')

            if not level_id or not academic_year_id:
                logger.warning(f"Missing level or academic_year for student {student.id}")
                return Response({
                    "student": serializer.data,
                    "warning": "Student created but not enrolled due to missing level or academic_year"
                }, status=status.HTTP_201_CREATED)

            try:
                level = Level.objects.get(id=level_id)
                academic_year = AcademicYear.objects.get(id=academic_year_id)

                # Create Enrollment
                enrollment = Enrollment.objects.create(
                    student=student,
                    level=level,
                    academic_year=academic_year,
                )
                logger.info(f"Created enrollment for student {student.id} in level {level.id}, year {academic_year.name}")

                # Create PassFailedStatus
                grades = Grade.objects.filter(enrollment=enrollment)
                subject_count = Subject.objects.filter(level=level).count()
                expected_grades = subject_count * 8 if subject_count else 1
                grades_complete = grades.exists()
                status_value = 'INCOMPLETE' if grades.count() < expected_grades else 'PENDING'

                pass_failed_status = PassFailedStatus.objects.create(
                    student=student,
                    level=level,
                    academic_year=academic_year,
                    enrollment=enrollment,
                    grades_complete=grades_complete,
                    status=status_value,
                    template_name='pass_template.html'
                )
                logger.info(f"Created PassFailedStatus for student {student.id}: {pass_failed_status.id}")

            except (Level.DoesNotExist, AcademicYear.DoesNotExist) as e:
                logger.error(f"Failed to enroll student {student.id}: {str(e)}")
                return Response({
                    "student": serializer.data,
                    "warning": f"Student created but not enrolled: {str(e)}"
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Unexpected error enrolling student {student.id}: {str(e)}")
                return Response({
                    "student": serializer.data,
                    "error": f"Failed to create enrollment or status: {str(e)}"
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
    

def get_students_by_level(level_id):
    """Fetch students by level ID."""
    return Student.objects.filter(enrollment__level_id=level_id).distinct()

def format_student_data(student):
    """Helper to format student data for grade sheets."""
    return {
        "student_id": student.id,
        "student_name": f"{student.firstName} {student.lastName}",
        "subjects": []
    }

def format_student_name(student):
    """Helper to format student name for grade retrieval."""
    return f"{student.firstName} {student.lastName}"

