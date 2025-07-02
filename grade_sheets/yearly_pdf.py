import logging
import os
from .yearly_student_pdf import generate_yearly_student_pdf
from .yearly_level_pdf import generate_yearly_level_pdf
from django.conf import settings

logger = logging.getLogger(__name__)

def generate_yearly_pdf(level_id, student_id=None, pass_template=True, conditional=False, academic_year=None):
    """
    Generate yearly report card PDFs for a student or level.
    
    Args:
        level_id: ID of the level.
        student_id: ID of the student (optional).
        pass_template: Use pass template (default True).
        conditional: Use conditional template (default False).
        academic_year: Academic year name (optional).
    
    Returns:
        List of PDF paths.
    """
    try:
        template_path = (
            os.path.join(settings.MEDIA_ROOT, 'templates', 'yearly_card_conditional.docx') if conditional else
            os.path.join(settings.MEDIA_ROOT, 'templates', 'yearly_card_pass.docx') if pass_template else
            os.path.join(settings.MEDIA_ROOT, 'templates', 'yearly_card_failed.docx')
        )
        if student_id:
            return generate_yearly_student_pdf(template_path, student_id, level_id, academic_year)
        else:
            return generate_yearly_level_pdf(level_id, academic_year)
    except Exception as e:
        logger.error(f"Error generating yearly PDF: {str(e)}")
        return []