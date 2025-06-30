import os
import time
import logging
import pythoncom
from itertools import islice
from docxtpl import DocxTemplate
from docx2pdf import convert
from PyPDF2 import PdfMerger
from django.conf import settings
from datetime import datetime
from levels.models import Level
from students.models import Student
from academic_years.models import AcademicYear
from enrollment.models import Enrollment
from pass_and_failed.models import PassFailedStatus
from grade_sheets.models import StudentGradeSheetPDF, LevelGradeSheetPDF
from grade_sheets.helpers import get_grade_sheet_data

logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(settings.MEDIA_ROOT, "output_gradesheets")
YEARLY_PASS_TEMPLATE = os.path.join(settings.MEDIA_ROOT, "templates", "yearly_card_pass.docx")
YEARLY_CONDITIONAL_TEMPLATE = os.path.join(settings.MEDIA_ROOT, "templates", "yearly_card_conditional.docx")
YEARLY_FAIL_TEMPLATE = os.path.join(settings.MEDIA_ROOT, "templates", "yearly_card_failed.docx")

def replace_placeholders(doc, data, semester=None):
    """
    Replace placeholders in the document for name and grades.
    
    Args:
        doc: Document object to modify.
        data: Student data from get_grade_sheet_data.
        semester: Ignored for yearly gradesheets (included for compatibility).
    """
    data = data.copy()
    if 'student_name' in data and 'name' not in data:
        data['name'] = data['student_name']

    key_mapping = {
        '1st': '1',
        '2nd': '2',
        '3rd': '3',
        '1exam': '1s',
        '1a': '1a',
        '4th': '4',
        '5th': '5',
        '6th': '6',
        '2exam': '2s',
        '2a': '2a',
        'f': 'f'
    }

    logger.debug(f"Data for placeholder replacement: {data}")

    for paragraph in doc.paragraphs:
        if '{{name}}' in paragraph.text:
            paragraph.text = paragraph.text.replace('{{name}}', str(data.get('name', '')))
            logger.debug(f"Replaced {{name}} with {data.get('name', '')} in paragraph: {paragraph.text}")

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                text = cell.text
                for i in range(9):
                    subject = data.get('s', [{}])[i] if i < len(data.get('s', [])) else {}
                    if f'{{{{s[{i}].sn}}}}' in text:
                        text = text.replace(f'{{{{s[{i}].sn}}}}', str(subject.get('sn', '')))
                        logger.debug(f"Replaced s[{i}].sn with {subject.get('sn', '')} in cell")
                    for data_key, template_key in key_mapping.items():
                        if f'{{{{s[{i}]["{template_key}"]}}}}' in text:
                            value = str(subject.get(data_key, '-'))
                            text = text.replace(f'{{{{s[{i}]["{template_key}"]}}}}', value)
                            logger.debug(f"Replaced s[{i}]['{template_key}'] with {value} in cell")
                cell.text = text
                logger.debug(f"Updated cell text: {cell.text}")

def generate_yearly_pdf(level_id, student_id=None, pass_template=True, conditional=False, academic_year=None):
    """
    Generate yearly report card PDFs using pass/conditional/failed templates.
    
    Args:
        level_id: ID of the level.
        student_id: ID of the student (optional).
        pass_template: Use pass template (default True).
        conditional: Use conditional template (default False).
        academic_year: Academic year name (optional).
    
    Returns:
        List of PDF paths (merged for level, single for student).
    """
    try:
        logger.debug(f"Starting yearly PDF generation for level_id={level_id}, student_id={student_id}, academic_year={academic_year}")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        if not os.access(OUTPUT_DIR, os.W_OK):
            raise PermissionError(f"No write permission for {OUTPUT_DIR}")

        pdf_paths = []
        enrollments = Enrollment.objects.filter(level_id=level_id)
        if academic_year:
            enrollments = enrollments.filter(academic_year__name=academic_year)
        students = [Student.objects.get(id=student_id)] if student_id else [e.student for e in enrollments]

        if not students:
            logger.warning(f"No students found for level_id: {level_id}, student_id: {student_id}, academic_year:{academic_year}")
            return pdf_paths

        if student_id:
            student = students[0]
            logger.debug(f"Processing student: {student.id}")
            student_data = get_grade_sheet_data(student.id, level_id, academic_year)
            logger.info(f"Prepared data for student: {student_data['name']}")

            status_obj = PassFailedStatus.objects.filter(student=student, level_id=level_id, academic_year__name=academic_year).first()
            template_path = YEARLY_CONDITIONAL_TEMPLATE if (status_obj and status_obj.status == 'CONDITIONAL') else \
                            YEARLY_PASS_TEMPLATE if (status_obj and status_obj.status == 'PASS') or pass_template else YEARLY_FAIL_TEMPLATE

            if not os.path.exists(template_path):
                logger.error(f"Template not found: {template_path}")
                return []

            doc = DocxTemplate(template_path)
            replace_placeholders(doc, student_data)
            student_name = student_data["name"].replace(" ", "_")
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            docx_path = os.path.join(OUTPUT_DIR, f"yearly_card_{student_name}_{timestamp}.docx")
            pdf_path = os.path.join(OUTPUT_DIR, f"yearly_card_{student_name}_{timestamp}.pdf")
            logger.debug(f"Output paths: docx={docx_path}, pdf={pdf_path}")

            if os.path.exists(docx_path) and not os.access(docx_path, os.W_OK):
                raise PermissionError(f"No write permission for {docx_path}")

            doc.save(docx_path)
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
                    StudentGradeSheetPDF.objects.create(
                        student=student,
                        level_id=level_id,
                        academic_year=AcademicYear.objects.get(name=academic_year) if academic_year else None,
                        pdf_path=pdf_path,
                        created_at=datetime.now()
                    )
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
            merger = PdfMerger()
            enrollment_pairs = list(islice(enrollments, 0, None, 2))
            for i in range(0, len(enrollments), 2):
                pair = enrollments[i:i+2]
                pair_pdf_paths = []
                for enrollment in pair:
                    student_data = get_grade_sheet_data(enrollment.student.id, level_id, academic_year)
                    logger.info(f"Prepared data for student: {student_data['name']}")

                    status_obj = PassFailedStatus.objects.filter(student=enrollment.student, level_id=level_id, academic_year__name=academic_year).first()
                    is_conditional = status_obj.status == 'CONDITIONAL' if status_obj else conditional
                    is_pass = status_obj.status in ['PASS', 'CONDITIONAL'] if status_obj else pass_template
                    template_path = YEARLY_CONDITIONAL_TEMPLATE if is_conditional else \
                                    YEARLY_PASS_TEMPLATE if is_pass else YEARLY_FAIL_TEMPLATE

                    if not os.path.exists(template_path):
                        logger.error(f"Template not found: {template_path}")
                        continue

                    doc = DocxTemplate(template_path)
                    replace_placeholders(doc, student_data)
                    student_name = student_data["name"].replace(" ", "_")
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    docx_path = os.path.join(OUTPUT_DIR, f"yearly_card_{student_name}_{timestamp}.docx")
                    pdf_path = os.path.join(OUTPUT_DIR, f"yearly_card_{student_name}_{timestamp}.pdf")
                    logger.debug(f"Output paths: docx={docx_path}, pdf={pdf_path}")

                    if os.path.exists(docx_path) and not os.access(docx_path, os.W_OK):
                        raise PermissionError(f"No write permission for {docx_path}")

                    doc.save(docx_path)
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
                            StudentGradeSheetPDF.objects.create(
                                student=enrollment.student,
                                level_id=level_id,
                                academic_year=AcademicYear.objects.get(name=academic_year) if academic_year else None,
                                pdf_path=pdf_path,
                                created_at=datetime.now()
                            )
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

                    pair_pdf_paths.append(pdf_path)

                if pair_pdf_paths:
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    merged_pdf_path = os.path.join(OUTPUT_DIR, f"yearly_cards_level_{level_id}_{timestamp}.pdf")
                    merger = PdfMerger()
                    for pdf_path in pair_pdf_paths:
                        merger.append(pdf_path)
                    if len(pair_pdf_paths) == 1:
                        merger.append(os.path.join(settings.MEDIA_ROOT, "templates", "blank_page.pdf"))
                    merger.write(merged_pdf_path)
                    merger.close()
                    logger.info(f"Merged PDFs into: {merged_pdf_path}")

                    if not os.path.exists(merged_pdf_path):
                        raise FileNotFoundError(f"Merged PDF not created: {merged_pdf_path}")
                    if os.path.getsize(merged_pdf_path) == 0:
                        raise ValueError(f"Merged PDF is empty: {merged_pdf_path}")

                    LevelGradeSheetPDF.objects.create(
                        level_id=level_id,
                        academic_year=AcademicYear.objects.get(name=academic_year) if academic_year else None,
                        pdf_path=merged_pdf_path,
                        created_at=datetime.now()
                    )
                    pdf_paths.append(merged_pdf_path)

                    for pdf_path in pair_pdf_paths:
                        try:
                            os.remove(pdf_path)
                            logger.info(f"Cleaned up individual PDF: {pdf_path}")
                        except Exception as e:
                            logger.warning(f"Failed to clean up PDF: {str(e)}")

            return pdf_paths

    except Exception as e:
        logger.error(f"Error generating yearly PDF: {str(e)}")
        return []