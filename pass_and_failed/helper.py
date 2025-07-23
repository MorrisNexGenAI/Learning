import datetime
from venv import logger
from rest_framework.response import Response
from django.db import transaction

from enrollment.utils import create_enrollment_for_student
from .models import PassFailedStatus
from enrollment.models import Enrollment
from academic_years.models import AcademicYear
from grades.models import Grade
from levels.models import Level
from subjects.models import Subject
from datetime import date, timedelta
from evaluations.promotional_logics import promote_student_if_eligible


def initialize_missing_statuses(level_id, academic_year_name, logger):
    try:
        level = Level.objects.get(id=level_id)
        academic_year = AcademicYear.objects.get(name=academic_year_name)
        enrollments = Enrollment.objects.filter(level=level, academic_year=academic_year)

        for enrollment in enrollments:
            if not PassFailedStatus.objects.filter(
                student=enrollment.student,
                level=level,
                academic_year=academic_year
            ).exists():
                grades = Grade.objects.filter(enrollment=enrollment)
                subject_count = Subject.objects.filter(level=level).count()
                expected_grades = subject_count * 8 if subject_count else 1
                grades_complete = grades.exists()
                status_value = 'INCOMPLETE' if grades.count() < expected_grades else 'PENDING'

                PassFailedStatus.objects.create(
                    student=enrollment.student,
                    level=level,
                    academic_year=academic_year,
                    enrollment=enrollment,
                    grades_complete=grades_complete,
                    status=status_value,
                    template_name='pass_template.html'
                )
                logger.info(f"Created PassFailedStatus for student {enrollment.student.id}, level {level.id}, year {academic_year.name}")

        return PassFailedStatus.objects.filter(
            student__in=[e.student_id for e in enrollments]
        )

    except (Level.DoesNotExist, AcademicYear.DoesNotExist) as e:
        logger.error(f"Error filtering statuses: {str(e)}")
        return PassFailedStatus.objects.none()
    except Exception as e:
        logger.error(f"Unexpected error in initialize_missing_statuses: {str(e)}")
        return PassFailedStatus.objects.none()


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
