from rest_framework import viewsets, status
from rest_framework.response import Response
from students.models import Student
from enrollment.models import Enrollment
from levels.models import Level
from students.serializers import StudentSerializer
import datetime

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def list(self, request, *args, **kwargs):
        level_id = request.query_params.get('level_id')
        queryset = get_students_by_level(level_id) if level_id else self.queryset
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        print(f"Received data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        print(f"Created student: {student.id} - {student.firstName} {student.lastName}")

        level_id = request.data.get('level')
        if level_id:
            try:
                level = Level.objects.get(id=level_id)
                enrollment, created = Enrollment.objects.get_or_create(
                    student=student,
                    level=level,
                    defaults={'academic_year': str(datetime.date.today().year)}
                )
                if created:
                    print(f"Enrollment created for student {student.id} in level {level.id}")
                else:
                    print(f"Enrollment already exists for student {student.id} in level {level.id}")
            except Level.DoesNotExist:
                print(f"Level {level_id} not found, skipping enrollment")
        else:
            print("No valid level data provided, skipping enrollment")

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=self.get_success_headers(serializer.data))

def get_students_by_level(level_id):
    """Fetch students by level ID."""
    return Student.objects.filter(enrollments__level_id=level_id).distinct()

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