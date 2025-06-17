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
from pass_and_failed.models import PassFailedStatus

logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(settings.MEDIA_ROOT, "output_gradesheets")
DEFAULT_TEMPLATE_PATH = os.path.join(settings.MEDIA_ROOT, "templates", "report_card_compact.docx")

def get_template_path(status):
    """
    Determine the template path based on the student's pass/fail status.
    
    Args:
        status (str): The pass/fail status (PASS, FAIL, CONDITIONAL, etc.).
    
    Returns:
        str: Path to the appropriate template.
    """
    template_map = {
        'PASS': os.path.join(settings.MEDIA_ROOT, "templates", "yearly_card_pass.docx"),
        'FAIL': os.path.join(settings.MEDIA_ROOT, "templates", "yearly_card_failed.docx"),
        'CONDITIONAL': os.path.join(settings.MEDIA_ROOT, "templates", "yearly_card_conditional.docx"),
    }
    template_path = template_map.get(status, DEFAULT_TEMPLATE_PATH)
    if not os.path.exists(template_path):
        logger.warning(f"Template {template_path} not found, falling back to default")
        template_path = DEFAULT_TEMPLATE_PATH
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Default template not found at {template_path}")
    return template_path

def generate_yearly_gradesheet_pdf(level_id, student_id=None, pass_template=True, academic_year=None):
    """
    Generate yearly report card PDFs for students in the given level_id or a single student_id.
    Uses yearly_card_pass.docx, yearly_card_failed.docx, or yearly_card_conditional.docx based on status.
    By Student: Single card with front/back pages.
    By Level: Pairs students on front/back sheets, two cards per sheet in a single docx.
    """
    try:
        logger.debug(f"Starting yearly PDF generation for level_id={level_id}, student_id={student_id}, academic_year={academic_year}")
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            logger.info(f"Created output directory: {OUTPUT_DIR}")

        if not os.access(OUTPUT_DIR, os.W_OK):
            raise PermissionError(f"No write permission for {OUTPUT_DIR}")

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

        if student_id:
            student = students[0]
            logger.debug(f"Processing student: {student.id}")
            student_data = get_grade_sheet_data(student.id, level_id, academic_year)
            logger.info(f"Prepared data for student: {student_data['name']}")

            status_obj = PassFailedStatus.objects.filter(student=student, level_id=level_id, academic_year__name=academic_year).first()
            template_path = get_template_path(status_obj.status if status_obj else ('PASS' if pass_template else 'FAIL'))

            student_name = student_data["name"].replace(" ", "_")
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            docx_path = os.path.join(OUTPUT_DIR, f"yearly_card_{student_name}_{timestamp}.docx")
            pdf_path = os.path.join(OUTPUT_DIR, f"yearly_card_{student_name}_{timestamp}.pdf")
            logger.debug(f"Output paths: docx={docx_path}, pdf={pdf_path}")

            if os.path.exists(docx_path) and not os.access(docx_path, os.W_OK):
                raise PermissionError(f"No write permission for {docx_path}")

            logger.debug("Rendering template")
            template = DocxTemplate(template_path)
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
            return pdf_paths

        else:
            for i in range(0, len(students), 2):
                pair = students[i:i+2]
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                pair_id = i // 2 + 1

                context = {}
                context["name1"] = get_grade_sheet_data(pair[0].id, level_id, academic_year)["name"]
                context["s1"] = get_grade_sheet_data(pair[0].id, level_id, academic_year)["s"]
                status1 = PassFailedStatus.objects.filter(student=pair[0], level_id=level_id, academic_year__name=academic_year).first()
                template_path = get_template_path(status1.status if status1 else 'PASS')

                if len(pair) == 2:
                    context["name2"] = get_grade_sheet_data(pair[1].id, level_id, academic_year)["name"]
                    context["s2"] = get_grade_sheet_data(pair[1].id, level_id, academic_year)["s"]
                    status2 = PassFailedStatus.objects.filter(student=pair[1], level_id=level_id, academic_year__name=academic_year).first()
                    if status2 and status2.status != status1.status:
                        logger.warning(f"Different statuses for pair {pair_id}, using template for first student")
                else:
                    context["name2"] = ""
                    context["s2"] = [
                        {"sn": "", "1": "-", "2": "-", "3": "-", "1s": "-", "4": "-", "5": "-", "6": "-", "2s": "-", "1a": "-", "2a": "-", "f": "-"}
                    ] * 9

                docx_path = os.path.join(OUTPUT_DIR, f"yearly_card_pair_{pair_id}_{timestamp}.docx")
                pdf_path = os.path.join(OUTPUT_DIR, f"yearly_card_pair_{pair_id}_{timestamp}.pdf")
                logger.debug(f"Rendering sheet: {docx_path}")
                template = DocxTemplate(template_path)
                template.render(context)
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

            if pdf_paths:
                merged_pdf_path = os.path.join(OUTPUT_DIR, f"yearly_cards_level_{level_id}_{timestamp}.pdf")
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
        logger.error(f"Error generating yearly PDF: {str(e)}")
        raise Exception(f"Error generating yearly PDF: {str(e)}")