from academic_years.models import AcademicYear
from students.helper import get_students_by_level
from grade_sheets.views import get_grade_map
from subjects.helper import get_subjects_by_level
from students.helper import format_student_data


def build_gradesheet(level_id, academic_year=None):
    academic_year_obj = AcademicYear.objects.get(name=academic_year) if academic_year else None
    students = get_students_by_level(level_id)
    if academic_year_obj:
        students = students.filter(enrollment__academic_year=academic_year_obj).distinct()
    grade_map = get_grade_map(level_id)
    subjects_by_id = get_subjects_by_level(level_id)

    result = []
    for student in students:
        student_data = format_student_data(student)
        subjects_data = {
            subject_id: {
                "subject_id": subject_id,
                "subject_name": subject_name,
                "1": None,
                "2": None,
                "3": None,
                "1s": None,
                "4": None,
                "5": None,
                "6": None,
                "2s": None,
                "1a": None,
                "2a": None,
                "f": None
            }
            for subject_id, subject_name in subjects_by_id.items()
        }

        for subject_id, grades in grade_map.get(student.id, {}).items():
            if subject_id in subjects_data:
                subjects_data[subject_id].update(grades)

        for subject_data in subjects_data.values():
            if all(subject_data.get(p) is not None for p in ["1", "2", "3", "1s"]):
                sem1_period_avg = (subject_data["1"] + subject_data["2"] + subject_data["3"]) // 3
                subject_data["1a"] = (sem1_period_avg + subject_data["1s"]) // 2
            if all(subject_data.get(p) is not None for p in ["4", "5", "6", "2s"]):
                sem2_period_avg = (subject_data["4"] + subject_data["5"] + subject_data["6"]) // 3
                subject_data["2a"] = (sem2_period_avg + subject_data["2s"]) // 2
            if subject_data["1a"] is not None and subject_data["2a"] is not None:
                subject_data["f"] = (subject_data["1a"] + subject_data["2a"]) // 2

        student_data["subjects"] = list(subjects_data.values())
        result.append(student_data)

    return result