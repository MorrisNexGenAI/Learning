import os
import logging
import uuid
from django.conf import settings
from docx import Document
from docx2pdf import convert
import pythoncom
from grade_sheets.pdf_utils import replace_placeholders
from grade_sheets.helpers import get_grade_sheet_data
from students.helper import get_students_by_level

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
        logger.info(f"Ensured directories exist: {output_dir}, {temp_dir}")

        # Verify directory permissions
        try:
            test_file = os.path.join(temp_dir, f"test_{uuid.uuid4()}.txt")
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            logger.info(f"Successfully tested write permissions in {temp_dir}")
        except PermissionError as e:
            logger.error(f"Permission error in {temp_dir}: {str(e)}")
            return []

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

        # Save the combined document with a unique filename
        temp_filename = f"temp_report_card_level_{level_id}_{academic_year_id}_{uuid.uuid4().hex}.docx"
        temp_path = os.path.join(temp_dir, temp_filename)
        try:
            combined_doc.save(temp_path)
            logger.info(f"Saved temporary combined DOCX: {temp_path}")
        except PermissionError as e:
            logger.error(f"Permission error saving {temp_path}: {str(e)}")
            return []

        # Initialize COM for docx2pdf
        pythoncom.CoInitialize()
        try:
            # Convert to PDF
            pdf_filename = f"level_{level_id}_{academic_year_id}.pdf"
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
            # Clean up temporary file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logger.info(f"Cleaned up temporary file: {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up {temp_path}: {str(e)}")

    except Exception as e:
        logger.error(f"Error generating level grade PDF: {str(e)}", exc_info=True)
        return []