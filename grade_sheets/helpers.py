from django.db.models import Q
from students.models import Student
from subjects.models import Subject
from grades.models import Grade
from enrollment.models import Enrollment
import logging

logger = logging.getLogger(__name__)

def get_grade_sheet_data(student_id, level_id, academic_year=None):
    logger.debug(f"Fetching grade sheet data for student_id={student_id}, level_id={level_id}, academic_year={academic_year}")
    try:
        student = Student.objects.get(id=student_id)
        subjects = Subject.objects.filter(level_id=level_id)
        
        # Filter grades by enrollment, level, and academic year
        grade_query = Grade.objects.filter(
            Q(enrollment__student__id=student_id) & 
            Q(subject__level_id=level_id)
        )
        
        if academic_year:
            grade_query = grade_query.filter(enrollment__academic_year__name=academic_year)
        
        grades = grade_query.select_related('subject', 'enrollment', 'period')

        logger.debug(f"Raw grades query for level {level_id}: {list(grades)}")

        subject_data = []
        for subject in subjects:
            subject_grades = {}
            for grade in grades.filter(subject_id=subject.id):
                logger.debug(f"Mapping grade: enrollment_id={grade.enrollment_id}, subject_id={grade.subject_id}, period={grade.period.period}, score={grade.score}")
                period_map = {
                    '1st': '1',
                    '2nd': '2',
                    '3rd': '3',
                    '1exam': '1s',
                    '4th': '4',
                    '5th': '5',
                    '6th': '6',
                    '2exam': '2s'
                }
                subject_grades[period_map.get(grade.period.period, grade.period.period)] = float(grade.score) if grade.score is not None else '-'

            data = {
                "id": subject.id,
                "sn": subject.subject,
                "1": subject_grades.get("1", ""),
                "2": subject_grades.get("2", ""),
                "3": subject_grades.get("3", ""),
                "1s": subject_grades.get("1s", ""),
                "4": subject_grades.get("4", ""),
                "5": subject_grades.get("5", ""),
                "6": subject_grades.get("6", ""),
                "2s": subject_grades.get("2s", ""),
                "1a": "",
                "2a": "",
                "f": ""
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