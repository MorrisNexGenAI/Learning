This is an overview of my backends.
it is divided into 9 django apps namely:academic_years, enrollment, grade_sheets, grades, levels, pass_and_failed, periods, students, and subjects.

But we are starting with enrollment first. i will share small explanation about each app along with the codes. the goal is to get a comprehensive view of it and an explanation to post on facebook for my thirty day journey. this is day 4. 

we will dive into the backend and then begins with the first app which is enrolment because it ties a student to a level and academic year which is crucial for a student identity within a level. 
each explanation will follow the question format
what is it?
why did i choose it?
and you can also brainstorm key questions that are engaging.
let start this is the general overview which is firt and then the enrollment:
OverView of the Backend:
🎓 Student Grading & Report Card System
 Designed to handle student enrollment, grading, report card generation (PDF/Word), academic evaluations, and flexible template rendering per school.

🧠 Backend Architecture – Django (Python)
The backend is organized into 9 modular Django apps, each serving a core part of the system:

1. enrollment
Connects students to levels and academic years. Serves as the bridge using foreign keys:

Student, Level, AcademicYear

Tracks: date_enrolled, status

2. grades
The core engine for storing and managing student scores.

Many-to-many logic: connects Enrollment, Subject, and Period

Tracks: score, updated_at

Includes: views, serializers, helper.py

3. grade_sheets
The heartbeat of the system, combining all logic to produce final report sheets.

Fields: student, level, academic_year, created_at, updated_at, pdf_path, filename

Includes: helpers, utils, pdf_utils, yearly_pdf_utils

4. students
The base model holding personal student information:

Fields: first_name, last_name, dob, gender, created_at

Includes: api/, views, serializers, helpers

5. levels
Represents digital classrooms (e.g., 7th grade, 8th grade):

Field: name (e.g., “Grade 9”)

Includes: views, serializers, helpers

6. subjects
Courses tied to specific levels.

Fields: subject, level (FK)

Includes: views, serializers, helpers

7. periods
Academic terms (e.g., 1st Term, 2nd Term, 1st Exam, etc.)

Fields: period, is_exam

Includes: views, serializers, helpers

8. pass_and_failed
Determines final student status and template to use.

STATUS_CHOICES: PASS, FAIL, CONDITIONAL, INCOMPLETE, PENDING

Tracks validation metadata and PDF template to use

Fields include: student, level, academic_year, status, template_name, etc.

9. academic_years
Defines school academic calendar years used throughout the system.

🧩 Core Technologies & Tools
Django REST Framework: API creation

pywin32: Word and PDF conversion via Windows COM interface (no WeasyPrint used)

Utils,Helper modules: Custom business logic per app

PDF generation: Uses .docx templates, converted to .pdf based on student pass/fail status

Custom api/ routing: All endpoints grouped in system/urls


1. enrollment: This is the part that connects a student to level and academic_year. it have a many to many keys, connecting and serving as bridge between student, level, and academic_year.
it have foreign keys to level, students, and academic_year, plus a model datefiled called date_enrolled and a model chatfield called status. 
The date enroll is use to track a student record consisting the date the student was enrolled in a specific level for a specific academic year.
The status is use to determine whether a student is enrolled or not.
enrollment has both views and serializers.



model.py:
from django.db import models
from students.models import Student
from levels.models import Level
from academic_years.models import AcademicYear

class Enrollment(models.Model):
    ENROLLMENT_STATUS_CHOICES = (
        ('ENROLLED', 'Enrolled'),
        ('WITHDRAWN', 'Withdrawn'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollment')
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    date_enrolled = models.DateField()
    enrollment_status = models.CharField(max_length=10, choices=ENROLLMENT_STATUS_CHOICES, default='ENROLLED')

    class Meta:
        unique_together = ('student', 'level', 'academic_year')

    def __str__(self):
        return f"{self.student} - {self.level} - {self.academic_year}"

views.py:
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



Serializer.py:from rest_framework import serializers
from .models import Enrollment
from students.models import Student
from levels.models import Level
from academic_years.models import AcademicYear

class EnrollmentSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all())
    level = serializers.PrimaryKeyRelatedField(queryset=Level.objects.all())
    academic_year = serializers.PrimaryKeyRelatedField(queryset=AcademicYear.objects.all())

    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'level', 'academic_year', 'date_enrolled', 'enrollment_status']


utils.py:import logging
from students.models import Student
from enrollment.models import Enrollment
from grades.models import Grade
from academic_years.models import AcademicYear
from enrollment.helper import get_enrollment_by_student_level
from grade_sheets.models import StudentGradeSheetPDF

logger = logging.getLogger(__name__)

def edit_student(student_id, level_id, academic_year, first_name=None, last_name=None, sex=None, delete=False):
    """
    Update or delete student details and invalidate affected PDFs.
    
    Args:
        student_id: ID of the student.
        level_id: ID of the level.
        academic_year: Academic year name.
        first_name: New first name (optional).
        last_name: New last name (optional).
        sex: New sex ('M' or 'F', optional).
        delete: If True, delete the enrollment (default False).
    
    Returns:
        Dict with response message and HTTP status.
    """
    if not all([student_id, level_id, academic_year]):
        return {
            "response": {"error": "student_id, level_id, and academic_year are required"},
            "status": 400
        }

    try:
        academic_year_obj = AcademicYear.objects.get(name=academic_year)
        student = Student.objects.get(id=student_id)
        enrollment = get_enrollment_by_student_level(student_id, level_id, academic_year_obj.id)
        if not enrollment:
            return {
                "response": {"error": f"No enrollment found for student_id={student_id}, level_id={level_id}, academic_year={academic_year}"},
                "status": 400
            }

        if delete:
            Grade.objects.filter(enrollment=enrollment).delete()
            StudentGradeSheetPDF.objects.filter(
                student_id=student_id,
                level_id=level_id,
                academic_year=academic_year_obj
            ).delete()
            enrollment.delete()
            logger.info(f"Deleted enrollment and grades for student_id={student_id}, level_id={level_id}, academic_year={academic_year}")
            return {
                "response": {"message": "Student enrollment deleted successfully"},
                "status": 200
            }

        updates = {}
        if first_name:
            updates['firstName'] = first_name
        if last_name:
            updates['lastName'] = last_name
        if sex:
            updates['gender'] = sex()
            if updates['gender'] not in ['M', 'F']:
                return {
                    "response": {"error": "sex must be 'M' or 'F'"},
                    "status": 400
                }

        if updates:
            Student.objects.filter(id=student_id).update(**updates)
            StudentGradeSheetPDF.objects.filter(
                student_id=student_id,
                level_id=level_id,
                academic_year=academic_year_obj
            ).delete()
            logger.info(f"Updated student details for student_id={student_id}: {updates}")
            return {
                "response": {"message": "Student details updated successfully"},
                "status": 200
            }

        return {
            "response": {"message": "No updates provided"},
            "status": 200
        }

    except Student.DoesNotExist:
        logger.error(f"Invalid student_id: {student_id}")
        return {
            "response": {"error": f"Invalid student_id: {student_id}"},
            "status": 400
        }
    except AcademicYear.DoesNotExist:
        logger.error(f"Invalid academic year: {academic_year}")
        return {
            "response": {"error": f"Invalid academic year: {academic_year}"},
            "status": 400
        }


helper.py:from .models import Enrollment

def get_enrollment_by_student_level(student_id, level_id, academic_year_id=None):
    """Fetch an enrollment by student, level, and optional academic year."""
    try:
        queryset = Enrollment.objects.filter(student_id=student_id, level_id=level_id)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        return queryset.first()
    except Enrollment.DoesNotExist:
        return None