from grade_sheets.helpers import get_grade_sheet_data
from subjects.models import Subject
from grades.models import Grade
from enrollment.models import Enrollment
from levels.models import Level
from academic_years.models import AcademicYear
import datetime
import logging

logger = logging.getLogger(__name__)

def validate_student_grades(student_id, level_id, academic_year_id):
    """
    Check if a student has complete grades for all subjects in a level and academic year.
    Returns: (is_complete, message)
    """
    try:
        # Fetch enrollment
        enrollment = Enrollment.objects.get(
            student_id=student_id, level_id=level_id, academic_year_id=academic_year_id
        )
        # Get grade sheet data
        grade_data = get_grade_sheet_data(student_id, level_id)
        subjects = Subject.objects.filter(level_id=level_id)
        required_periods = ['1', '2', '3', '1s', '4', '5', '6', '2s']  # Simplified periods
        required_averages = ['1a', '2a', 'f']  # Simplified averages (1a=1sa, 2a=2sa, f=fa)

        # Check if all subjects have grades
        for subject in subjects:
            subject_data = next((s for s in grade_data['s'] if s['sn'] == subject.subject), None)
            if not subject_data:
                return False, f"Missing grades for subject: {subject.subject}"
            for period in required_periods:
                if subject_data.get(period) in [None, '', '-']:
                    return False, f"Missing grade for {subject.subject} in period {period}"
            for avg in required_averages:
                if subject_data.get(avg) in [None, '', '-']:
                    return False, f"Missing {avg} average for {subject.subject}"

        return True, "All grades and averages complete"
    except Enrollment.DoesNotExist:
        return False, "No enrollment found for student"
    except Exception as e:
        logger.error(f"Error validating grades for student {student_id}: {str(e)}")
        return False, str(e)

def promote_student(status_id):
    """
    Promote a student to the next level and academic year if status is PASS or CONDITIONAL.
    Returns: (success, message)
    """
    try:
        from pass_and_failed.models import PassFailedStatus
        status = PassFailedStatus.objects.get(id=status_id)
        if status.status not in ['PASS', 'CONDITIONAL']:
            return False, "Only PASS or CONDITIONAL students can be promoted"

        current_level = status.level
        current_academic_year = status.academic_year
        student = status.student

        # Get next level
        current_level_id = int(current_level.name)  # Assuming name is '7', '8', '9'
        next_level_id = current_level_id + 1
        if next_level_id > 9:  # Max level
            return False, "Student is at the highest level (9)"

        next_level = Level.objects.filter(name=str(next_level_id)).first()
        if not next_level:
            return False, f"Next level {next_level_id} does not exist"

        # Get next academic year
        current_year = current_academic_year.name  # e.g., '2025/2026'
        start_year = int(current_year.split('/')[0]) + 1
        next_year_name = f"{start_year}/{start_year + 1}"
        next_academic_year = AcademicYear.objects.filter(name=next_year_name).first()
        if not next_academic_year:
            return False, f"Next academic year {next_year_name} does not exist"

        # Create new enrollment
        enrollment, created = Enrollment.objects.get_or_create(
            student=student,
            level=next_level,
            academic_year=next_academic_year,
            defaults={'date_enrolled': datetime.date.today()}
        )
        if created:
            logger.info(f"Promoted {student} to level {next_level}, academic year {next_academic_year}")
            return True, f"Promoted to level {next_level}, academic year {next_academic_year}"
        else:
            return False, "Enrollment already exists"
    except Exception as e:
        logger.error(f"Error promoting student {status.student}: {str(e)}")
        return False, str(e)