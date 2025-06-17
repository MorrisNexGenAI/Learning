import os
import logging
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg
from grades.models import Grade
from subjects.models import Subject
from .models import GradeSheetPDF

logger = logging.getLogger(__name__)

def cleanup_old_pdfs(days=2):
    """
    Delete PDF files and their database records older than the specified number of days.
    
    Args:
        days (int): Number of days to consider for cleanup. Defaults to 2.
    """
    cutoff = timezone.now() - timedelta(days=days)
    old_pdfs = GradeSheetPDF.objects.filter(updated_at__lt=cutoff)
    for pdf_record in old_pdfs:
        if os.path.exists(pdf_record.pdf_path):
            try:
                os.remove(pdf_record.pdf_path)
                logger.info(f"Deleted old PDF: {pdf_record.pdf_path}")
            except Exception as e:
                logger.error(f"Failed to delete PDF {pdf_record.pdf_path}: {str(e)}")
        pdf_record.delete()

def determine_pass_fail(student_id, level_id, academic_year=None, passing_score=50):
    """
    Determine pass/fail/incomplete status for a student given level and academic year.
    Conditions:
    - All subjects must have at least 8 grades recorded.
    - Average score per subject must be >= passing_score.
    - If any subject has < 8 grades or no grades, status = INCOMPLETE.
    - If any subject average < passing_score, status = FAILED.
    - Otherwise, status = PASSED.
    """
    try:
        # Get all subjects for the level
        subjects = Subject.objects.filter(level_id=level_id)
        if not subjects.exists():
            logger.warning(f"No subjects found for level {level_id}")
            return "INCOMPLETE"

        for subject in subjects:
            # Filter grades for this student, subject, level, and optionally academic year
            grade_query = Grade.objects.filter(
                enrollment__student_id=student_id,
                subject=subject,
                enrollment__level_id=level_id
            )
            if academic_year:
                grade_query = grade_query.filter(enrollment__academic_year__name=academic_year)

            grade_count = grade_query.count()
            if grade_count < 8:
                logger.debug(f"Subject {subject.subject} has incomplete grades ({grade_count} < 8)")
                return "INCOMPLETE"

            avg_score = grade_query.aggregate(avg=Avg('score'))['avg']
            if avg_score is None:
                logger.debug(f"Subject {subject.subject} has no scores recorded")
                return "INCOMPLETE"
            if avg_score < passing_score:
                logger.debug(f"Subject {subject.subject} failed with avg score {avg_score}")
                return "FAILED"

        logger.info(f"Student {student_id} passed level {level_id} for year {academic_year}")
        return "PASSED"

    except Exception as e:
        logger.error(f"Error determining pass/fail for student {student_id}: {str(e)}")
        return "INCOMPLETE"