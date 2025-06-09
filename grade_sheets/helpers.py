from django.db.models import Q
from students.models import Student
from subjects.models import Subject
from grades.models import Grade
import logging

logger = logging.getLogger(__name__)

def get_grade_sheet_data(student_id, level_id):
    logger.debug(f"Fetching grade sheet data for student_id={student_id}, level_id={level_id}")
    try:
        student = Student.objects.get(id=student_id)
        subjects = Subject.objects.filter(level_id=level_id)
        grades = Grade.objects.filter(
            Q(enrollment__student__id=student_id) & Q(subject__level_id=level_id)
        ).select_related('subject', 'enrollment', 'period')

        logger.debug(f"Raw grades query for level {level_id}: {list(grades)}")

        subject_data = []
        for subject in subjects:
            subject_grades = {}
            for grade in grades.filter(subject_id=subject.id):
                logger.debug(f"Mapping grade: enrollment_id={grade.enrollment_id}, subject_id={grade.subject_id}, period={grade.period.period}, score={grade.score}")
                period_map = {
                    '1st': '1st',
                    '2nd': '2nd',
                    '3rd': '3rd',
                    '1exam': '1se',
                    '4th': '4th',
                    '5th': '5th',
                    '6th': '6th',
                    '2exam': '2se'
                }
                subject_grades[period_map.get(grade.period.period, grade.period.period)] = float(grade.score) if grade.score is not None else '-'

            data = {
                "id": subject.id,
                "sn": subject.subject,
                "1st": subject_grades.get("1st", "-"),
                "2nd": subject_grades.get("2nd", "-"),
                "3rd": subject_grades.get("3rd", "-"),
                "1se": subject_grades.get("1se", "-"),
                "4th": subject_grades.get("4th", "-"),
                "5th": subject_grades.get("5th", "-"),
                "6th": subject_grades.get("6th", "-"),
                "2se": subject_grades.get("2se", "-"),
                "1sa": "-",
                "2sa": "-",
                "fa": "-"
            }
            subject_data.append(data)

        grade_sheet_data = {
            "name": f"{student.firstName} {student.lastName}",
            "s": subject_data
        }
        logger.info(f"Grade sheet data for student {student_id}, level {level_id}: {grade_sheet_data}")
        return grade_sheet_data
    except Exception as e:
        logger.error(f"Error generating grade sheet data: {str(e)}")
        raise