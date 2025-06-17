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

def calc_semester_avg(scores, exam):
    if not scores or exam is None:
        return None
    total = sum(scores)
    count = len(scores)
    total += exam
    count += 1
    return round(total / count, 2) if count > 0 else None

def calc_final_avg(sem1_avg, sem2_avg):
    if sem1_avg is None or sem2_avg is None:
        return None
    return round((sem1_avg + sem2_avg) / 2, 2)

def save_grade(enrollment: Enrollment, subject_id: int, period_id: int, score: float, request=None) -> tuple:
    if not period_id:
        logger.error(f"Period ID is null for enrollment_id={enrollment.id}, subject_id={subject_id}")
        return None, {"period": ["This field may not be null."]}

    try:
        period = Period.objects.get(id=period_id)
    except Period.DoesNotExist:
        logger.error(f"Invalid period_id={period_id}")
        return None, {"period_id": ["Invalid period ID."]}

    try:
        subject = Subject.objects.get(id=subject_id)
    except Subject.DoesNotExist:
        logger.error(f"Invalid subject_id={subject_id}")
        return None, {"subject_id": ["Invalid subject ID."]}

    try:
        if not (0 <= score <= 100):
            logger.error(f"Invalid score={score} for enrollment_id={enrollment.id}, subject_id={subject_id}, period_id={period_id}")
            return None, {"score": ["Score must be between 0 and 100."]}

        grade, created = Grade.objects.update_or_create(
            enrollment=enrollment,
            subject=subject,
            period=period,
            defaults={'score': score}
        )
        logger.info(f"{'Saved' if created else 'Updated'} grade: id={grade.id}, enrollment_id={enrollment.id}, subject_id={subject.id}, period_id={period.id}, score={score}")
        return grade, None

    except ValidationError as e:
        logger.error(f"Validation error saving grade: {str(e)}")
        return None, {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error saving grade: {str(e)}")
        return None, str(e)
