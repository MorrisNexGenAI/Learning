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