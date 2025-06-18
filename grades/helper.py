from grades.models import Grade
from subjects.models import Subject
from periods.models import Period
from django.core.exceptions import ValidationError
from enrollment.models import Enrollment
import logging

logger = logging.getLogger(__name__)

def get_grade_map(level_id):
    grades = Grade.objects.filter(enrollment__level_id=level_id).select_related('enrollment__student', 'subject', 'period')
    grade_map = {}

    for grade in grades:
        student_id = grade.enrollment.student_id
        subject_id = grade.subject_id
        period = grade.period.period.lower()

        if period in ["1st semester exam", "first semester exam"]:
            period = "1exam"
        elif period in ["2nd semester exam", "second semester exam"]:
            period = "2exam"
        elif period in ["1st", "2nd", "3rd", "4th", "5th", "6th"]:
            period = period

        score = float(grade.score) if grade.score is not None else None

        if student_id not in grade_map:
            grade_map[student_id] = {}
        if subject_id not in grade_map[student_id]:
            grade_map[student_id][subject_id] = {}

        grade_map[student_id][subject_id][period] = score

    return grade_map

def calc_semester_avg(period_scores, exam_score, level_id):
    """Calculate semester average with configurable weights."""
    from .models import GradePolicy
    if not all(score is not None for score in period_scores + [exam_score]):
        return None
    policy = GradePolicy.objects.filter(level_id=level_id).first()
    period_weight = policy.period_weight if policy else 0.5
    exam_weight = policy.exam_weight if policy else 0.5
    period_avg = sum(period_scores) / len(period_scores)
    return round((period_avg * period_weight + exam_score * exam_weight), 2)

def calc_final_avg(sem1_avg, sem2_avg):
    """Calculate final average."""
    if sem1_avg is None or sem2_avg is None:
        return None
    return round((sem1_avg + sem2_avg) / 2, 2)

def save_grade(enrollment, subject_id, period_id, score, request):
    """Create or update a grade."""
    from subjects.models import Subject
    from periods.models import Period
    try:
        subject = Subject.objects.get(id=subject_id)
        period = Period.objects.get(id=period_id)
        if not (0 <= score <= 100):
            return None, f"Invalid score {score} for {subject.subject} in {period.period}. Score must be between 0 and 100."
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