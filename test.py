import os
import django
from docxtpl import DocxTemplate
from grade_sheets.helpers import get_grade_sheet_data

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grade_system.settings')
django.setup()

template_path = r"C:\Users\User\Desktop\GradeSheet\grade_system\media\templates\report_card_minimal.docx"
output_docx = r"C:\Users\User\Desktop\GradeSheet\grade_system\media\output_gradesheets\test_render_minimal.docx"
student_data = get_grade_sheet_data(22, 28)
template = DocxTemplate(template_path)
template.render(student_data)
template.save(output_docx)
print(f"Rendered .docx saved to {output_docx}")

