import os
import time
import logging
import pythoncom
from docx2pdf import convert
from PyPDF2 import PdfMerger
from django.conf import settings
from docx import Document
from enrollment.models import Enrollment
from .helpers import get_grade_sheet_data
from .models import StudentGradeSheetPDF, LevelGradeSheetPDF
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_gradesheet_pdf(level_id, student_id=None, academic_year_id=None):
    """Generate PDF grade sheets for a level or student using Word templates."""
    from levels.models import Level
    from students.models import Student
    from academic_years.models import AcademicYear
    try:
        pythoncom.CoInitialize()
        level = Level.objects.get(id=level_id)
        academic_year = AcademicYear.objects.get(id=academic_year_id) if academic_year_id else None
        pdf_paths = []
        output_dir = os.path.join(settings.MEDIA_ROOT, 'output_gradesheets')
        os.makedirs(output_dir, exist_ok=True)
        template_path = os.path.join(settings.MEDIA_ROOT, 'templates', 'report_card_compact.docx')

        if not os.path.exists(template_path):
            logger.error(f"Template not found: {template_path}")
            return []

        def replace_placeholders(doc, data):
            """Replace only {{name}} and grade-related placeholders in the document."""
            # Map student_name to name
            data = data.copy()
            if 'student_name' in data and 'name' not in data:
                data['name'] = data['student_name']

            # Map data keys to template placeholders
            key_mapping = {
                '1st': '1',
                '2nd': '2',
                '3rd': '3',
                '1exam': '1s',
                '4th': '4',
                '5th': '5',
                '6th': '6',
                '2exam': '2s',
                '1a': '1a',
                '1sa': '1sa',
                '2a': '2a',
                'f': 'f'
            }

            # Log data for debugging
            logger.debug(f"Data for placeholder replacement: {data}")

            # Replace student name in paragraphs
            for paragraph in doc.paragraphs:
                if '{{name}}' in paragraph.text:
                    paragraph.text = paragraph.text.replace('{{name}}', str(data.get('name', '')))
                    logger.debug(f"Replaced {{name}} with {data.get('name', '')} in paragraph: {paragraph.text}")

            # Replace subject data in tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text = cell.text
                        for i in range(9):  # Support up to 9 subjects
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

        if student_id:
            student = Student.objects.get(id=student_id)
            data = get_grade_sheet_data(student_id, level_id, academic_year_id)
            logger.debug(f"Grade sheet data for student_id={student_id}: {data}")
            if not data:
                logger.warning(f"No data for student_id={student_id}")
                return []
            doc = Document(template_path)
            replace_placeholders(doc, data)
            docx_path = os.path.join(output_dir, f"temp_{student.firstName}_{student.lastName}_{int(time.time())}.docx")
            pdf_path = os.path.join(output_dir, f"report_card_{student.firstName}_{student.lastName}_{academic_year.name}.pdf")
            try:
                doc.save(docx_path)
                logger.info(f"Saved DOCX: {docx_path}")
            except PermissionError as e:
                logger.error(f"Permission denied saving {docx_path}: {str(e)}")
                return []
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    pythoncom.CoInitialize()
                    convert(docx_path, pdf_path)
                    logger.info(f"Generated PDF: {pdf_path}")
                    StudentGradeSheetPDF.objects.create(
                        student=student,
                        level=level,
                        academic_year=academic_year,
                        pdf_path=pdf_path,
                        created_at=datetime.now()
                    )
                    break
                except Exception as e:
                    logger.error(f"PDF conversion attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(2)
                finally:
                    pythoncom.CoUninitialize()
            try:
                # Commented out for debugging
                # os.remove(docx_path)
                pass
            except PermissionError as e:
                logger.warning(f"Could not delete {docx_path}: {str(e)}")
            if os.path.exists(pdf_path):
                pdf_paths.append(pdf_path)
            else:
                logger.error(f"PDF not created: {pdf_path}")
                return []
        else:
            merger = PdfMerger()
            enrollments = Enrollment.objects.filter(level_id=level_id, academic_year_id=academic_year_id)
            for enrollment in enrollments:
                data = get_grade_sheet_data(enrollment.student.id, level_id, academic_year_id)
                logger.debug(f"Grade sheet data for student_id={enrollment.student.id}: {data}")
                if not data:
                    logger.warning(f"No data for student_id={enrollment.student.id}")
                    continue
                doc = Document(template_path)
                replace_placeholders(doc, data)
                docx_path = os.path.join(output_dir, f"temp_{enrollment.student.firstName}_{enrollment.student.lastName}_{int(time.time())}.docx")
                pdf_path = os.path.join(output_dir, f"report_card_{enrollment.student.firstName}_{enrollment.student.lastName}_{academic_year.name}.pdf")
                try:
                    doc.save(docx_path)
                    logger.info(f"Saved DOCX: {docx_path}")
                except PermissionError as e:
                    logger.error(f"Permission denied saving {docx_path}: {str(e)}")
                    continue
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        pythoncom.CoInitialize()
                        convert(docx_path, pdf_path)
                        logger.info(f"Generated PDF: {pdf_path}")
                        StudentGradeSheetPDF.objects.create(
                            student=enrollment.student,
                            level=level,
                            academic_year=academic_year,
                            pdf_path=pdf_path,
                            created_at=datetime.now()
                        )
                        break
                    except Exception as e:
                        logger.error(f"PDF conversion attempt {attempt + 1} failed: {str(e)}")
                        if attempt == max_retries - 1:
                            raise
                        time.sleep(2)
                    finally:
                        pythoncom.CoUninitialize()
                try:
                    # Commented out for debugging
                    # os.remove(docx_path)
                    pass
                except PermissionError as e:
                    logger.warning(f"Could not delete {docx_path}: {str(e)}")
                if os.path.exists(pdf_path):
                    merger.append(pdf_path)
                    pdf_paths.append(pdf_path)
            if pdf_paths:
                merged_pdf_path = os.path.join(output_dir, f"level_{level.name}_{academic_year.name}.pdf")
                merger.write(merged_pdf_path)
                merger.close()
                if os.path.exists(merged_pdf_path):
                    LevelGradeSheetPDF.objects.create(
                        level=level,
                        academic_year=academic_year,
                        pdf_path=merged_pdf_path,
                        created_at=datetime.now()
                    )
                    pdf_paths.append(merged_pdf_path)
                else:
                    logger.error(f"Merged PDF not created: {merged_pdf_path}")

        return pdf_paths
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        return []
    finally:
        pythoncom.CoUninitialize()