from grades.models import Grade, GradePolicy
from enrollment.models import Enrollment
from subjects.models import Subject
from .models import StudentGradeSheetPDF, LevelGradeSheetPDF
import os
from datetime import datetime, timedelta

def cleanup_old_pdfs(days=2):
    """Delete PDFs older than specified days."""
    cutoff = datetime.now() - timedelta(days=days)
    for model in [StudentGradeSheetPDF, LevelGradeSheetPDF]:
        old_pdfs = model.objects.filter(created_at__lt=cutoff)
        for pdf in old_pdfs:
            if os.path.exists(pdf.pdf_path):
                os.remove(pdf.pdf_path)
        old_pdfs.delete()

def determine_pass_fail(student_id, level_id, academic_year_id):
    """Calculate pass/fail status based on grades."""
    try:
        enrollment = Enrollment.objects.get(student_id=student_id, level_id=level_id, academic_year_id=academic_year_id)
        grades = Grade.objects.filter(enrollment=enrollment)
        subjects = Subject.objects.filter(level_id=level_id)
        policy = GradePolicy.objects.filter(level_id=level_id).first()
        required_grades = policy.required_grades if policy else 8
        passing_threshold = policy.passing_threshold if policy else 50

        if not grades.exists():
            return 'INCOMPLETE'
        for subject in subjects:
            subject_grades = grades.filter(subject=subject)
            if subject_grades.count() < required_grades:
                return 'INCOMPLETE'
            avg_score = sum(g.score for g in subject_grades) / subject_grades.count()
            if avg_score < passing_threshold:
                return 'FAILED'
        return 'PASSED'
    except Enrollment.DoesNotExist:
        return 'INCOMPLETE'
    
import logging
from grades.models import Grade
from academic_years.models import AcademicYear
from enrollment.helper import get_enrollment_by_student_level
from .models import StudentGradeSheetPDF

logger = logging.getLogger(__name__)

def update_grades(level_id, subject_id, period_id, grades, academic_year):
    """
    Update existing grades and invalidate affected PDFs.
    
    Args:
        level_id: ID of the level.
        subject_id: ID of the subject.
        period_id: ID of the period.
        grades: List of grade data (student_id, score).
        academic_year: Academic year name.
    
    Returns:
        Dict with response message and HTTP status.
    """
    if not isinstance(grades, list):
        grades = []
        for key, value in grades.items():
            if key.startswith('grades[') and value:
                student_id = key.split('[')[1].split(']')[0]
                grades.append({'student_id': student_id, 'score': value})

    if not all([level_id, subject_id, period_id, academic_year]) or not isinstance(grades, list):
        return {
            "response": {"error": "Missing or invalid required fields, including academic_year."},
            "status": 400
        }

    try:
        academic_year_obj = AcademicYear.objects.get(id=academic_year)
         
        updated_grades = []
        skipped_students = []
        errors = []
        affected_student_ids = []

        for grade_data in grades:
            student_id = grade_data.get('student_id')
            score = grade_data.get('score')
            if not student_id or score is None:
                errors.append({"student_id": student_id, "error": "Missing student_id or score"})
                continue

            try:
                score = int(score)
                if not (0 <= score <= 100):
                    errors.append({"student_id": student_id, "error": "Score must be an integer between 0 and 100"})
                    continue
            except (ValueError, TypeError):
                errors.append({"student_id": student_id, "error": "Score must be an integer"})
                continue

            enrollment = get_enrollment_by_student_level(student_id, level_id, academic_year_obj.id)
            if not enrollment:
                logger.warning(f"No enrollment found for student_id={student_id}, level_id={level_id}, academic_year={academic_year}")
                skipped_students.append(student_id)
                continue

            grade = Grade.objects.filter(
                enrollment=enrollment,
                subject_id=subject_id,
                period_id=period_id
            ).first()
            if not grade:
                errors.append({"student_id": student_id, "error": "Grade does not exist"})
                continue

            grade.score = score
            grade.save()
            updated_grades.append(grade.id)
            affected_student_ids.append(student_id)
            logger.info(f"Updated grade: id={grade.id}, enrollment_id={enrollment.id}, subject_id={subject_id}, period_id={period_id}, score={score}")

        if updated_grades:
            StudentGradeSheetPDF.objects.filter(
                level_id=level_id,
                student_id__in=affected_student_ids,
                academic_year=academic_year_obj
            ).delete()
            logger.info(f"Deleted existing PDFs for students {affected_student_ids} due to updated grades.")

        response_data = {
            "message": "Grades updated.",
            "updated_grades": updated_grades,
            "skipped_students": skipped_students,
            "errors": errors
        }
        status_code = 200 if updated_grades else 400
        if errors:
            response_data["message"] = "Some grades failed to update."
            status_code = 400
        return {
            "response": response_data,
            "status": status_code
        }

    except AcademicYear.DoesNotExist:
        logger.error(f"Invalid academic year: {academic_year}")
        return {
            "response": {"error": f"Invalid academic year: {academic_year}"},
            "status": 400
        }