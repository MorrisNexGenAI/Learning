import os
import logging
from django.conf import settings
from .yearly_student_pdf import generate_yearly_student_pdf
from .yearly_level_pdf import generate_yearly_level_pdf
from pass_and_failed.models import PassFailedStatus

logger = logging.getLogger(__name__)

def generate_yearly_pdf(level_id, student_id=None, pass_template=True, conditional=False, academic_year_id=None):
    """
    Generate yearly report card PDFs for a student or level.
    
    Args:
        level_id: ID of the level.
        student_id: ID of the student (optional).
        pass_template: Use pass template (default True).
        conditional: Use conditional template (default False).
        academic_year_id: ID of the academic year (optional).
    
    Returns:
        List of PDF paths.
    """
    try:
        os.makedirs(os.path.join(settings.MEDIA_ROOT, "output_gradesheets"), exist_ok=True)
        
        # Determine template based on PassFailedStatus if student_id is provided
        if student_id:
            try:
                status_obj = PassFailedStatus.objects.get(
                    student_id=student_id,
                    level_id=level_id,
                    academic_year_id=academic_year_id
                )
                pass_template = status_obj.status in ['PASS', 'CONDITIONAL']
                conditional = status_obj.status == 'CONDITIONAL'
                logger.debug(f"Using status {status_obj.status}: pass_template={pass_template}, conditional={conditional}")
            except PassFailedStatus.DoesNotExist:
                logger.warning(f"No PassFailedStatus found for student_id={student_id}, level_id={level_id}, academic_year_id={academic_year_id}")
                pass_template = True  # Fallback to pass template
                conditional = False

        if student_id:
            return generate_yearly_student_pdf(level_id, student_id, academic_year_id, pass_template, conditional)
        else:
            return generate_yearly_level_pdf(level_id, academic_year_id, pass_template, conditional)
    except Exception as e:
        logger.error(f"Error generating yearly PDF: {str(e)}")
        return []