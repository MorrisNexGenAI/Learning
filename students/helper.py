from .models import Student
from enrollment.models import Enrollment
from pass_and_failed.models import PassFailedStatus
from grades.models import Grade
from levels.models import Level
from academic_years.models import AcademicYear
import datetime
import logging

logger = logging.getLogger(__name__)

def get_students_by_level(level_id, academic_year_id=None):
    """Fetch students by level ID, optionally filtered by academic year."""
    queryset = Student.objects.filter(enrollment__level_id=level_id)
    if academic_year_id:
        queryset = queryset.filter(enrollment__academic_year_id=academic_year_id)
    return queryset.distinct()

def format_student_data(student):
    """Format student data for use in grade sheets."""
    return {
        "student_id": student.id,
        "student_name": f"{student.firstName} {student.lastName}",
        "subjects": []
    }

def format_student_name(student):
    """Format student full name."""
    return f"{student.firstName} {student.lastName}"

def clean_duplicate_students(firstName, lastName, dob, level_id):
    """Delete students with the same name/dob not enrolled in the given level."""
    students = Student.objects.filter(
        firstName = firstName,
        lastName = lastName,
        dob = dob
    )
    deleted = []
    for student in students:
        if not student.enrollment.filter(level_id=level_id).exists():
            deleted.append(student.id)
            student.delete()
    print(f"Deleted students with IDs: {deleted}")
    return deleted