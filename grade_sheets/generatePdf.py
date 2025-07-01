import os
import logging
from django.conf import settings
from grade_sheets.periodic_pdf import generate_grade_pdf
from grade_sheets.periodic_level_pdf import generate_periodic_level_pdf
from grade_sheets.yearly_pdf import generate_yearly_pdf

logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(settings.MEDIA_ROOT, "output_gradesheets")
DEFAULT_TEMPLATE_PATH = os.path.join(settings.MEDIA_ROOT, "templates", "report_card_compact.docx")
YEARLY_PASS_TEMPLATE = os.path.join(settings.MEDIA_ROOT, "templates", "yearly_card_pass.docx")
YEARLY_CONDITIONAL_TEMPLATE = os.path.join(settings.MEDIA_ROOT, "templates", "yearly_card_conditional.docx")
YEARLY_FAIL_TEMPLATE = os.path.join(settings.MEDIA_ROOT, "templates", "yearly_card_failed.docx")

def get_template_path(template_name=None, is_yearly=False, pass_template=True, conditional=False):
    """
    Validate and return the template path, falling back to default periodic template unless yearly is specified.
    
    Args:
        template_name (str): Path to the template.
        is_yearly (bool): Flag to indicate yearly context (default False).
        pass_template (bool): Use pass template for yearly gradesheets.
        conditional (bool): Use conditional template for yearly gradesheets.
    
    Returns:
        str: Valid template path.
    """
    if template_name and os.path.exists(template_name):
        return template_name
    logger.warning(f"Template {template_name} not found, selecting default")
    # Default to periodic template unless yearly context is specified
    template_path = DEFAULT_TEMPLATE_PATH if not is_yearly else (
        YEARLY_CONDITIONAL_TEMPLATE if conditional else
        (YEARLY_PASS_TEMPLATE if pass_template else YEARLY_FAIL_TEMPLATE)
    )
    if not os.path.exists(template_path):
        logger.error(f"Template not found at {template_path}, falling back to default")
        template_path = DEFAULT_TEMPLATE_PATH
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found at {template_path}")
    logger.debug(f"Selected template: {template_path}")
    return template_path

def generate_gradesheet_pdf(level_id, student_id=None, academic_year_id=None):
    """
    Generate periodic PDF grade sheets for a student or level.
    
    Args:
        level_id: ID of the level.
        student_id: ID of the student (optional).
        academic_year_id: ID of the academic year (optional).
    
    Returns:
        List of PDF paths.
    """
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        template_path = get_template_path(is_yearly=False)
        if student_id:
            # Generate for a single student
            return generate_grade_pdf(template_path, student_id, level_id, academic_year_id)
        else:
            # Generate for all students in the level
            return generate_periodic_level_pdf(template_path, level_id, academic_year_id)
    except Exception as e:
        logger.error(f"Error generating periodic PDF: {str(e)}")
        return []

def generate_yearly_gradesheet_pdf(level_id, student_id=None, pass_template=True, conditional=False, academic_year=None):
    """
    Generate yearly report card PDFs by calling yearly_pdf.py.
    
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
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        return generate_yearly_pdf(level_id, student_id, pass_template, conditional, academic_year)
    except Exception as e:
        logger.error(f"Error generating yearly PDF: {str(e)}")
        return []