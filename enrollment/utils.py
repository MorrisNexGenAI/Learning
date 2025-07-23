
import datetime
from venv import logger
from .models import Enrollment


def create_enrollment_for_student(student, level, academic_year):
    """Create an enrollment record."""
    try:
        return Enrollment.objects.create(
            student=student,
            level=level,
            academic_year=academic_year,
            date_enrolled=academic_year.start_date or datetime.date.today(),
            enrollment_status='ENROLLED'
        )
    except Exception as e:
        logger.error(f"Error creating enrollment for student {student.id}: {str(e)}")
        raise
