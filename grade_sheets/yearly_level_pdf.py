import os
import logging
import pythoncom
from docxtpl import DocxTemplate
from docx2pdf import convert
from PyPDF2 import PdfMerger
from django.conf import settings
from grade_sheets.helpers import get_grade_sheet_data
from pass_and_failed.models import PassFailedStatus
from enrollment.models import Enrollment
from .models import LevelGradeSheetPDF
from academic_years.models import AcademicYear
from datetime import datetime
from .yearly_student_pdf import replace_placeholders

logger = logging.getLogger(__name__)

def generate_yearly_level_pdf(level_id, academic_year):
    """Generate a single PDF for all students in a level, with each student on a separate page."""
    try:
        output_dir = os.path.join(settings.MEDIA_ROOT, 'output_gradesheets')
        os.makedirs(output_dir, exist_ok=True)

        enrollments = Enrollment.objects.filter(level_id=level_id, academic_year__name=academic_year)
        if not enrollments.exists():
            logger.warning(f"No enrollments found for level_id={level_id}, academic_year={academic_year}")
            return []

        merger = PdfMerger()
        temp_pdf_paths = []
        for enrollment in enrollments:
            student_id = enrollment.student.id
            student_data = get_grade_sheet_data(student_id, level_id, academic_year)
            if not student_data or 'name' not in student_data:
                logger.warning(f"No data found for student_id={student_id}")
                continue

            status_obj = PassFailedStatus.objects.filter(student_id=student_id, level_id=level_id, academic_year__name=academic_year).first()
            template_path = (
                os.path.join(settings.MEDIA_ROOT, 'templates', 'yearly_card_conditional.docx') if status_obj and status_obj.status == 'CONDITIONAL' else
                os.path.join(settings.MEDIA_ROOT, 'templates', 'yearly_card_pass.docx') if status_obj and status_obj.status == 'PASS' else
                os.path.join(settings.MEDIA_ROOT, 'templates', 'yearly_card_failed.docx')
            )

            if not os.path.exists(template_path):
                logger.error(f"Template not found: {template_path}")
                continue

            doc = DocxTemplate(template_path)
            replace_placeholders(doc, student_data)
            student_name = student_data['name'].replace(' ', '_').replace(':', '_').replace('/', '_').replace('\\', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            docx_path = os.path.join(output_dir, f"temp_yearly_card_{student_name}_{timestamp}.docx")
            temp_pdf_path = os.path.join(output_dir, f"temp_yearly_card_{student_name}_{timestamp}.pdf")

            doc.save(docx_path)
            logger.info(f"Saved .docx: {docx_path}")

            pythoncom.CoInitialize()
            try:
                convert(docx_path, temp_pdf_path)
                logger.info(f"Converted to PDF: {temp_pdf_path}")
            finally:
                pythoncom.CoUninitialize()

            if not os.path.exists(temp_pdf_path):
                logger.error(f"PDF not created at {temp_pdf_path}")
                continue

            temp_pdf_paths.append(temp_pdf_path)
            try:
                os.remove(docx_path)
                logger.info(f"Cleaned up .docx: {docx_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up .docx: {str(e)}")

        if not temp_pdf_paths:
            logger.warning(f"No PDFs generated for level_id={level_id}, academic_year={academic_year}")
            return []

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        merged_pdf_path = os.path.join(output_dir, f"yearly_cards_level_{level_id}_{timestamp}.pdf")
        for temp_pdf_path in temp_pdf_paths:
            merger.append(temp_pdf_path)
        if len(temp_pdf_paths) % 2 == 1:
            merger.append(os.path.join(settings.MEDIA_ROOT, 'templates', 'blank_page.pdf'))
        merger.write(merged_pdf_path)
        merger.close()
        logger.info(f"Merged PDFs into: {merged_pdf_path}")

        if not os.path.exists(merged_pdf_path):
            logger.error(f"Merged PDF not created: {merged_pdf_path}")
            return []

        LevelGradeSheetPDF.objects.create(
            level_id=level_id,
            academic_year=AcademicYear.objects.get(name=academic_year),
            pdf_path=merged_pdf_path,
            filename=os.path.basename(merged_pdf_path),
            created_at=datetime.now()
        )

        for temp_pdf_path in temp_pdf_paths:
            try:
                os.remove(temp_pdf_path)
                logger.info(f"Cleaned up temp PDF: {temp_pdf_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp PDF: {str(e)}")

        return [merged_pdf_path]

    except Exception as e:
        logger.error(f"Error generating yearly level PDF: {str(e)}")
        return []