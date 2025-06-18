import logging
from .models import Grade
from subjects.models import Subject
from periods.models import Period

logger = logging.getLogger(__name__)

def save_grade(enrollment, subject_id, period_id, score, request):
    """Create or update a grade."""
    try:
        subject = Subject.objects.get(id=subject_id)
        period = Period.objects.get(id=period_id)
        if not isinstance(score, int) or not (0 <= score <= 100):
            return None, f"Invalid score {score} for {subject.subject} in {period.period}. Score must be an integer between 0 and 100."
        grade, created = Grade.objects.update_or_create(
            enrollment=enrollment,
            subject=subject,
            period=period,
            defaults={'score': score}
        )
        logger.info(f"{'Created' if created else 'Updated'} grade: {grade.id}")
        return grade, None
    except Subject.DoesNotExist:
        logger.error(f"Subject {subject_id} not found")
        return None, f"Subject ID {subject_id} does not exist."
    except Period.DoesNotExist:
        logger.error(f"Period {period_id} not found")
        return None, f"Period ID {period_id} does not exist."
    except Exception as e:
        logger.error(f"Error saving grade: {str(e)}")
        return None, f"Failed to save grade: {str(e)}"

def get_grade_map(enrollment_ids, subject_id, period_id):
    """Fetch grades for given enrollments, subject, and period."""
    grades = Grade.objects.filter(
        enrollment_id__in=enrollment_ids,
        subject_id=subject_id,
        period_id=period_id
    ).select_related('enrollment__student')
    return {grade.enrollment.student.id: grade.score for grade in grades}