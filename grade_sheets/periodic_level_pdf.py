from docx import Document
import os
import logging
from django.conf import settings
from grade_sheets.helpers import get_grade_sheet_data
from students.helper import get_students_by_level
from docx2pdf import convert
from grade_sheets.pdf_utils import replace_placeholders
import pythoncom

logger = logging.getLogger(__name__)

def generate_periodic_level_pdf(template_path, level_id, academic_year_id):
    """Generate a single PDF for all students in a level, with each student on a separate page."""
    try:
        if not os.path.exists(template_path):
            logger.error(f"Template not found: {template_path}")
            raise FileNotFoundError(f"Template not found: {template_path}")

        output_dir = os.path.join(settings.MEDIA_ROOT, 'output_gradesheets')
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)

        # Get all students for the level
        students = get_students_by_level(level_id)
        if not students:
            logger.warning(f"No students found for level_id={level_id}")
            return []

        # Create a single document for all students
        combined_doc = Document()
        first_student = True

        for student in students:
            # Get student data
            data = get_grade_sheet_data(student_id=student.id, level_id=level_id, academic_year_id=academic_year_id)
            if not data or 'name' not in data:
                logger.warning(f"No data found for student_id={student.id}, level_id={level_id}, academic_year_id={academic_year_id}")
                continue

            # Load template for this student
            template_doc = Document(template_path)
            # Replace placeholders
            template_doc = replace_placeholders(template_doc, data)

            # Copy content to combined document
            for element in template_doc.element.body:
                combined_doc.element.body.append(element)

            # Add page break between students (except for the first one)
            if not first_student:
                combined_doc.add_page_break()
            first_student = False

            logger.info(f"Processed grade sheet for student {student.id}: {data.get('name', 'Unknown')}")

        # Save the combined document
        temp_filename = f"temp_report_card_level_{level_id}_{academic_year_id}.docx"
        temp_path = os.path.join(temp_dir, temp_filename)
        combined_doc.save(temp_path)
        logger.info(f"Saved temporary combined DOCX: {temp_path}")

        # Initialize COM for docx2pdf
        pythoncom.CoInitialize()
        try:
            # Convert to PDF
            pdf_filename = temp_filename.replace('.docx', '.pdf')
            pdf_path = os.path.join(output_dir, pdf_filename)
            convert(temp_path, pdf_path)
            if os.path.exists(pdf_path):
                logger.info(f"PDF generated for level {level_id}: {pdf_path}")
                return [pdf_path]
            else:
                logger.error(f"PDF not created at {pdf_path}")
                return []
        finally:
            pythoncom.CoUninitialize()

    except Exception as e:
        logger.error(f"Error generating level grade PDF: {str(e)}")
        return []