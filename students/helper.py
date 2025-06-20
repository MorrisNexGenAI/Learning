from .models import Student
from enrollment.models import Enrollment
from pass_and_failed.models import PassFailedStatus
from grades.models import Grade
from levels.models import Level
from academic_years.models import AcademicYear
from django.db import transaction
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

def create_pass_failed_status(student, level, academic_year, enrollment, status='PENDING', validated_by=None):
    """Create or update pass/fail/conditional status with manual assignment and promotion."""
    valid_statuses = [choice[0] for choice in PassFailedStatus.STATUS_CHOICES]
    if status not in valid_statuses:
        logger.error(f"Invalid status: {status} for student {student.id}")
        raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

    grades_complete = Grade.objects.filter(enrollment=enrollment).exists()
    if not grades_complete and status in ['PASS', 'FAIL', 'CONDITIONAL']:
        logger.error(f"Cannot set {status} for student {student.id}: grades incomplete")
        raise ValueError(f"Cannot set {status} status: grades are incomplete for student {student.id}")

    with transaction.atomic():
        # Create or update PassFailedStatus
        pass_failed, created = PassFailedStatus.objects.update_or_create(
            student=student,
            level=level,
            academic_year=academic_year,
            enrollment=enrollment,
            defaults={
                'status': status,
                'grades_complete': grades_complete,
                'validated_by': validated_by,
                'validated_at': datetime.datetime.now() if validated_by else None
            }
        )

        # Promotion for PASS or COND
        if status in ['PASS', 'CONDITIONAL']:
            try:
                current_level_id = int(level.name)
                next_level_id = current_level_id + 1
                if next_level_id > 9:  # Assuming max level is 9
                    logger.warning(f"No promotion for student {student.id}: at max level {current_level_id}")
                    return pass_failed

                next_level = Level.objects.filter(name=str(next_level_id)).first()
                if not next_level:
                    logger.error(f"Next level {next_level_id} not found for student {student.id}")
                    raise ValueError(f"Next level {next_level_id} does not exist")

                current_year = academic_year.name
                start_year = int(current_year.split('/')[0]) + 1
                next_year_name = f"{start_year}/{start_year + 1}"
                next_academic_year = AcademicYear.objects.filter(name=next_year_name).first()
                if not next_academic_year:
                    logger.error(f"Next academic year {next_year_name} not found for student {student.id}")
                    raise ValueError(f"Academic year {next_year_name} does not exist")

                # Check for existing enrollment to avoid unique_together violation
                existing_enrollment = Enrollment.objects.filter(
                    student=student,
                    level=next_level
                ).first()
                if not existing_enrollment:
                    create_enrollment_for_student(student, next_level, next_academic_year)
                    logger.info(f"Promoted student {student.id} to level {next_level.name}, year {next_year_name}")
                else:
                    logger.warning(f"Enrollment already exists for student {student.id} in level {next_level.name}")

            except ValueError as e:
                logger.error(f"Error promoting student {student.id}: {str(e)}")
                raise

        logger.info(f"{'Created' if created else 'Updated'} PassFailedStatus for student {student.id}: {status}")
        return pass_failed

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
    
from students.models import Student

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