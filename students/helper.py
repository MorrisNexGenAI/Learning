from .models import Student
from enrollment.models import Enrollment
from pass_and_failed.models import PassFailedStatus
from grades.models import Grade
from subjects.models import Subject

def get_students_by_level(level_id):
    """Fetch students by level ID."""
    return Student.objects.filter(enrollment__level_id=level_id).distinct()

def format_student_data(student):
    """Format student data for use in grade sheets."""
    return {
        "student_id": student.id,
        "student_name": f"{student.firstName} {student.lastName}",
        "subjects": []  # To be populated externally
    }

def format_student_name(student):
    """Format student full name."""
    return f"{student.firstName} {student.lastName}"

def create_enrollment_for_student(student, level, academic_year):
    """Create an enrollment record."""
    return Enrollment.objects.create(
        student=student,
        level=level,
        academic_year=academic_year
    )

def create_pass_failed_status(student, level, academic_year, enrollment):
    """Auto-create pass/fail status for a student."""
    grades = Grade.objects.filter(enrollment=enrollment)
    subject_count = Subject.objects.filter(level=level).count()
    expected_grades = subject_count * 8 if subject_count else 1
    grades_complete = grades.exists()
    status_value = 'INCOMPLETE' if grades.count() < expected_grades else 'PENDING'

    return PassFailedStatus.objects.create(
        student=student,
        level=level,
        academic_year=academic_year,
        enrollment=enrollment,
        grades_complete=grades_complete,
        status=status_value,
        template_name='pass_template.html'
    )
