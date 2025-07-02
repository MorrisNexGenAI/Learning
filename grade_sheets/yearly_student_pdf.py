import os
import logging
import pythoncom
from docxtpl import DocxTemplate
from docx2pdf import convert
from django.conf import settings
from grade_sheets.helpers import get_grade_sheet_data
from pass_and_failed.models import PassFailedStatus
from .models import StudentGradeSheetPDF
from academic_years.models import AcademicYear
from datetime import datetime

logger = logging.getLogger(__name__)

def replace_placeholders(doc, data):
    """
    Replace placeholders in the document for name and grades.
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

def generate_yearly_student_pdf(template_path, student_id, level_id, academic_year):
    """Generate PDF for a single student with yearly grades."""
    try:
        output_dir = os.path.join(settings.MEDIA_ROOT, 'output_gradesheets')
        os.makedirs(output_dir, exist_ok=True)

        student_data = get_grade_sheet_data(student_id, level_id, academic_year)
        if not student_data or 'name' not in student_data:
            logger.warning(f"No data found for student_id={student_id}, level_id={level_id}, academic_year={academic_year}")
            return []

        status_obj = PassFailedStatus.objects.filter(student_id=student_id, level_id=level_id, academic_year__name=academic_year).first()
        template_path = (
            os.path.join(settings.MEDIA_ROOT, 'templates', 'yearly_card_conditional.docx') if status_obj and status_obj.status == 'CONDITIONAL' else
            os.path.join(settings.MEDIA_ROOT, 'templates', 'yearly_card_pass.docx') if status_obj and status_obj.status == 'PASS' else
            os.path.join(settings.MEDIA_ROOT, 'templates', 'yearly_card_failed.docx')
        )

        if not os.path.exists(template_path):
            logger.error(f"Template not found: {template_path}")
            return []

        doc = DocxTemplate(template_path)
        replace_placeholders(doc, student_data)
        student_name = student_data['name'].replace(' ', '_').replace(':', '_').replace('/', '_').replace('\\', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        docx_path = os.path.join(output_dir, f"yearly_card_{student_name}_{timestamp}.docx")
        pdf_path = os.path.join(output_dir, f"yearly_card_{student_name}_{timestamp}.pdf")

        doc.save(docx_path)
        logger.info(f"Saved .docx: {docx_path}")

        pythoncom.CoInitialize()
        try:
            convert(docx_path, pdf_path)
            logger.info(f"Converted to PDF: {pdf_path}")
        finally:
            pythoncom.CoUninitialize()

        if not os.path.exists(pdf_path):
            logger.error(f"PDF not created at {pdf_path}")
            return []

        student = get_grade_sheet_data(student_id, level_id, academic_year)
        StudentGradeSheetPDF.objects.create(
            student_id=student_id,
            level_id=level_id,
            academic_year=AcademicYear.objects.get(name=academic_year),
            pdf_path=pdf_path,
            filename=os.path.basename(pdf_path),
            created_at=datetime.now()
        )

        try:
            os.remove(docx_path)
            logger.info(f"Cleaned up .docx: {docx_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up .docx: {str(e)}")

        return [pdf_path]

    except Exception as e:
        logger.error(f"Error generating yearly student PDF: {str(e)}")
        return []