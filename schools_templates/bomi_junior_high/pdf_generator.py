from django.http import HttpResponse
from django.template.loader import get_template
from django.conf import settings
import subprocess
import os
from grades.models import Grade
from subjects.views import get_subjects_by_level
from students.views import get_students_by_level

def generate_gradesheet_pdf(student_id, level_id):
    # Fetch data
    student = get_students_by_level(student_id)
    grades = Grade.objects.filter(enrollment__student_id=student_id, enrollment__level_id=level_id)
    subjects = get_subjects_by_level(level_id)

    # Prepare grade data
    grade_data = {}
    for grade in grades:
        subject_id = grade.subject_id
        period = grade.period.period.lower()
        if period in ["1st semester exam", "first semester exam"]:
            period = "1exam"
        elif period in ["2nd semester exam", "second semester exam"]:
            period = "2exam"
        elif period in ["1st", "2nd", "3rd", "4th", "5th", "6th"]:
            period = period

        if subject_id not in grade_data:
            grade_data[subject_id] = {
                "1st": None, "2nd": None, "3rd": None, "1exam": None,
                "4th": None, "5th": None, "6th": None, "2exam": None,
                "sem1_avg": None, "sem2_avg": None, "final_avg": None
            }
        grade_data[subject_id][period] = float(grade.score) if grade.score is not None else None

    # Calculate averages
    for subject_id, data in grade_data.items():
        sem1_scores = [data.get(p) for p in ["1st", "2nd", "3rd"] if data.get(p) is not None]
        sem1_exam = data.get("1exam")
        if sem1_scores and sem1_exam is not None:
            data["sem1_avg"] = round((sum(sem1_scores) / len(sem1_scores) + sem1_exam) / 2, 1)

        sem2_scores = [data.get(p) for p in ["4th", "5th", "6th"] if data.get(p) is not None]
        sem2_exam = data.get("2exam")
        if sem2_scores and sem2_exam is not None:
            data["sem2_avg"] = round((sum(sem2_scores) / len(sem2_scores) + sem2_exam) / 2, 1)

        if data["sem1_avg"] is not None and data["sem2_avg"] is not None:
            data["final_avg"] = round((data["sem1_avg"] + data["sem2_avg"]) / 2, 1)

    # Prepare context for all subjects
    subjects_list = [
        {
            "name": subjects.get(subject_id, f"Subject {subject_id}"),
            "grades": grade_data.get(subject_id, {
                "1st": None, "2nd": None, "3rd": None, "1exam": None,
                "4th": None, "5th": None, "6th": None, "2exam": None,
                "sem1_avg": None, "sem2_avg": None, "final_avg": None
            })
        }
        for subject_id in subjects.keys()
    ]

    # Resolve logo path
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'schools', 'bomi-junior-high', 'images', 'bomi-logo.png')
    logo_path = logo_path.replace('\\', '/')  # Normalize path for LaTeX

    context = {
        "student_name": f"{student.firstName} {student.lastName}",
        "level_id": level_id,
        "subjects": subjects_list,
        "logo_path": logo_path,
    }

    # Render LaTeX template
    template_path = 'schools_templates/bomi-junior-high/pdf_templates/gradesheet.tex'
    tex_content = get_template(template_path).render(context)

    # Write to temporary file
    tex_file = f"C:/tmp/gradesheet_{student_id}.tex"
    os.makedirs(os.path.dirname(tex_file), exist_ok=True)
    with open(tex_file, 'w', encoding='utf-8') as f:
        f.write(tex_content)

    # Compile to PDF
    pdf_file = f"C:/tmp/gradesheet_{student_id}.pdf"
    subprocess.run(['latexmk', '-pdf', tex_file], check=True, cwd=os.path.dirname(tex_file))

    # Read and return PDF
    with open(pdf_file, 'rb') as f:
        pdf_content = f.read()

    # Clean up
    for file in [tex_file, pdf_file]:
        if os.path.exists(file):
            os.remove(file)

    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="gradesheet_{student_id}.pdf"'
    return response