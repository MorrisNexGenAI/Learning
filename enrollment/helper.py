from venv import logger
from .models import Enrollment

def get_enrollment_by_student_level(student_id, level_id, academic_year_id=None):
    """Fetch an enrollment by student, level, and optional academic year."""
    try:
        queryset = Enrollment.objects.filter(student_id=student_id, level_id=level_id)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        return queryset.first()
    except Enrollment.DoesNotExist:
        return None


def get_enrollment_for_student_year(student_id, academic_year_id, level_id):
    """Fetch enrollment for a student in a specific academic year and level."""
    try:
        return Enrollment.objects.filter(
            student_id=student_id,
            academic_year_id=academic_year_id,
            level_id=level_id
        ).select_related('student').first()
    except Exception as e:
        logger.error(f"Error fetching enrollment for student {student_id}: {str(e)}")
        return None