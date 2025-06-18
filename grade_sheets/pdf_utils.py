import os
import pythoncom
from docx2pdf import convert
from PyPDF2 import PdfMerger
from django.conf import settings
from .helper import get_grade_sheet_data
from docx import Document

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
        template_path = os.path.join(settings.BASE_DIR, 'templates', 'grade_sheets', 'report_card_compact.docx')

        if student_id:
            student = Student.objects.get(id=student_id)
            data = get_grade_sheet_data(student_id, level_id, academic_year_id)
            if not data:
                return []
            doc = Document(template_path)
            # Populate doc with data (simplified example)
            for paragraph in doc.paragraphs:
                if '{{student_name}}' in paragraph.text:
                    paragraph.text = paragraph.text.replace('{{student_name}}', data['student_name'])
            docx_path = os.path.join(output_dir, f"temp_{student.firstName}_{student.lastName}.docx")
            doc.save(docx_path)
            pdf_path = os.path.join(output_dir, f"report_card_{student.firstName}_{student.lastName}_{academic_year.name}.pdf")
            convert(docx_path, pdf_path)
            os.remove(docx_path)
            pdf_paths.append(pdf_path)
        else:
            merger = PdfMerger()
            enrollments = Enrollment.objects.filter(level_id=level_id, academic_year_id=academic_year_id)
            for enrollment in enrollments:
                data = get_grade_sheet_data(enrollment.student.id, level_id, academic_year_id)
                if not data:
                    continue
                doc = Document(template_path)
                for paragraph in doc.paragraphs:
                    if '{{student_name}}' in paragraph.text:
                        paragraph.text = paragraph.text.replace('{{student_name}}', data['student_name'])
                docx_path = os.path.join(output_dir, f"temp_{enrollment.student.firstName}_{enrollment.student.lastName}.docx")
                doc.save(docx_path)
                pdf_path = os.path.join(output_dir, f"report_card_{enrollment.student.firstName}_{enrollment.student.lastName}_{academic_year.name}.pdf")
                convert(docx_path, pdf_path)
                os.remove(docx_path)
                merger.append(pdf_path)
                pdf_paths.append(pdf_path)
            if pdf_paths:
                merged_pdf_path = os.path.join(output_dir, f"level_{level.name}_{academic_year.name}.pdf")
                merger.write(merged_pdf_path)
                merger.close()
                pdf_paths.append(merged_pdf_path)

        pythoncom.CoUninitialize()
        return pdf_paths
    except Exception as e:
        pythoncom.CoUninitialize()
        print(f"Error generating PDF: {str(e)}")
        return []