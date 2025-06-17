import os
import time
import logging
import pythoncom
from django.conf import settings
from docxtpl import DocxTemplate
from docx2pdf import convert
from PyPDF2 import PdfMerger
from grade_sheets.helpers import get_grade_sheet_data
from students.models import Student
from enrollment.models import Enrollment

logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(settings.MEDIA_ROOT, "output_gradesheets")
TEMPLATE_PATH = os.path.join(settings.MEDIA_ROOT, "templates", "report_card_compact.docx")

def generate_gradesheet_pdf(level_id, student_id=None, academic_year=None):
    """
    Generate individual report card PDFs using report_card_compact.docx for students in the given level_id or a single student_id.
    Returns a list of generated PDF paths or a single merged PDF path for bulk printing.
    """
    try:
        logger.debug(f"Starting PDF generation for level_id={level_id}, student_id={student_id}, academic_year={academic_year}")
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            logger.info(f"Created output directory: {OUTPUT_DIR}")

        if not os.access(OUTPUT_DIR, os.W_OK):
            raise PermissionError(f"No write permission for {OUTPUT_DIR}")

        if not os.path.exists(TEMPLATE_PATH):
            raise FileNotFoundError(f"Template not found at {TEMPLATE_PATH}")
        logger.info(f"Using template: {TEMPLATE_PATH}")

        pdf_paths = []
        if student_id:
            student = Student.objects.get(id=student_id)
            enrollments = Enrollment.objects.filter(student_id=student_id, level_id=level_id)
            if academic_year:
                enrollments = enrollments.filter(academic_year__name=academic_year)
            students = [student] if enrollments.exists() else []
        else:
            enrollments = Enrollment.objects.filter(level_id=level_id).select_related("student")
            if academic_year:
                enrollments = enrollments.filter(academic_year__name=academic_year)
            students = [enrollment.student for enrollment in enrollments]

        if not students:
            logger.warning(f"No students found for level_id: {level_id}, student_id: {student_id}, academic_year:{academic_year}")
            return pdf_paths

        for student in students:
            logger.debug(f"Processing student: {student.id}")
            student_data = get_grade_sheet_data(student.id, level_id, academic_year)
            logger.info(f"Prepared data for student: {student_data['name']}")

            student_name = student_data["name"].replace(" ", "_")
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            docx_path = os.path.join(OUTPUT_DIR, f"report_card_{student_name}_{timestamp}.docx")
            pdf_path = os.path.join(OUTPUT_DIR, f"report_card_{student_name}_{timestamp}.pdf")
            logger.debug(f"Output paths: docx={docx_path}, pdf={pdf_path}")

            if os.path.exists(docx_path) and not os.access(docx_path, os.W_OK):
                raise PermissionError(f"No write permission for {docx_path}")

            logger.debug("Rendering template")
            template = DocxTemplate(TEMPLATE_PATH)
            template.render(student_data)
            template.save(docx_path)
            logger.info(f"Saved .docx: {docx_path}")

            if not os.path.exists(docx_path):
                raise FileNotFoundError(f"Failed to create .docx at {docx_path}")
            if os.path.getsize(docx_path) == 0:
                raise ValueError(f"Generated .docx is empty: {docx_path}")

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    pythoncom.CoInitialize()
                    logger.debug(f"Attempt {attempt + 1}: Converting {docx_path} to {pdf_path}")
                    convert(docx_path, pdf_path)
                    logger.info(f"Converted to PDF: {pdf_path}")
                    break
                except Exception as e:
                    logger.error(f"PDF conversion attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        raise Exception(f"PDF conversion failed after {max_retries} attempts: {str(e)}")
                    time.sleep(2)
                finally:
                    pythoncom.CoUninitialize()

            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF generation failed for {pdf_path}")
            if os.path.getsize(pdf_path) == 0:
                raise ValueError(f"Generated PDF is empty: {pdf_path}")

            try:
                os.remove(docx_path)
                logger.info(f"Cleaned up .docx: {docx_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up .docx: {str(e)}")

            pdf_paths.append(pdf_path)

        if not student_id and pdf_paths:
            merged_pdf_path = os.path.join(OUTPUT_DIR, f"report_cards_level_{level_id}_{timestamp}.pdf")
            merger = PdfMerger()
            for pdf_path in pdf_paths:
                merger.append(pdf_path)
            merger.write(merged_pdf_path)
            merger.close()
            logger.info(f"Merged PDFs into: {merged_pdf_path}")

            if not os.path.exists(merged_pdf_path):
                raise FileNotFoundError(f"Merged PDF not created: {merged_pdf_path}")
            if os.path.getsize(merged_pdf_path) == 0:
                raise ValueError(f"Merged PDF is empty: {merged_pdf_path}")

            for pdf_path in pdf_paths:
                try:
                    os.remove(pdf_path)
                    logger.info(f"Cleaned up individual PDF: {pdf_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up PDF: {str(e)}")

            return [merged_pdf_path]

        return pdf_paths

    except Exception as e:
        logger.error(f"Error generating gradesheet PDF: {str(e)}")
        raise Exception(f"Error generating gradesheet PDF: {str(e)}")