from docx import Document
import os
import logging
from django.conf import settings
from grade_sheets.periodic_student_pdf import generate_student_grade_pdf
from grade_sheets.periodic_level_pdf import generate_periodic_level_pdf

logger = logging.getLogger(__name__)

def generate_grade_pdf(template_path, student_id, level_id, academic_year_id):
    """Render grade PDFs by delegating to student or level generation."""
    try:
        if student_id:
            # Generate PDF for a single student
            return generate_student_grade_pdf(template_path, student_id, level_id, academic_year_id)
        else:
            # Generate PDFs for all students in the level
            return generate_periodic_level_pdf(template_path, level_id, academic_year_id)
    except Exception as e:
        logger.error(f"Error in generate_grade_pdf: {str(e)}")
        return []