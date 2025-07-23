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
