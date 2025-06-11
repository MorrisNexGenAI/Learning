from rest_framework import viewsets, status
from rest_framework.response import Response
from students.models import Student
from enrollment.models import Enrollment
from levels.models import Level
from students.serializers import StudentSerializer
import datetime
from academic_years.models import AcademicYear

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def list(self, request, *args, **kwargs):
        level_id = request.query_params.get('level_id')
        academic_year = request.query_params.get('academic_year')
        queryset = self.queryset
        if level_id:
            queryset = queryset.filter(enrollment__level_id=level_id).distinct()
        if academic_year:
            queryset = queryset.filter(enrollment__academic_year__name=academic_year).distinct()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        print(f"Received data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()

        level_id = request.data.get('level')
        academic_year_id = request.data.get('academic_year')
        if level_id and academic_year_id:
            try:
                level = Level.objects.get(id=level_id)
                academic_year = AcademicYear.objects.get(id=academic_year_id)
                enrollment, created = Enrollment.objects.get_or_create(
                    student=student,
                    level=level,
                    academic_year=academic_year,
                    defaults={'date_enrolled': datetime.date.today()}
                )
                if created:
                    print(f"Enrollment created for student {student.id} in level {level.id}, academic year {academic_year.name}")
                else:
                    print(f"Enrollment already exists for student {student.id} in level {level.id}, academic year {academic_year.name}")
            except (Level.DoesNotExist, AcademicYear.DoesNotExist):
                print(f"Level {level_id} or Academic Year {academic_year_id} not found, skipping enrollment")
        else:
            print("No valid level or academic year data provided, skipping enrollment")

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=self.get_success_headers(serializer.data))

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
