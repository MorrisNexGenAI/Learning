from grades.models import Grade
from subjects.models import Subject
from enrollment.models import Enrollment
from .utils import determine_pass_fail
from periods.models import Period

def get_grade_sheet_data(student_id, level_id, academic_year_id=None):
    """Compile grade data for a student, level, and optional academic year."""
    try:
        enrollment = Enrollment.objects.get(student_id=student_id, level_id=level_id, academic_year_id=academic_year_id)
        grades = Grade.objects.filter(enrollment=enrollment).select_related('subject', 'period')
        subjects = Subject.objects.filter(level_id=level_id)
        periods = Period.objects.all()
        period_map = {p.period: p.period for p in periods}  # Use actual period codes

        grade_data = {
            'student_name': f"{enrollment.student.firstName} {enrollment.student.lastName}",
            's': [],  # Subjects
            'status': determine_pass_fail(student_id, level_id, academic_year_id)
        }

        for subject in subjects:
            subject_grades = {'sn': subject.subject}
            for period in periods:
                grade = grades.filter(subject=subject, period=period).first()
                subject_grades[period.period] = grade.score if grade else '-'
            grade_data['s'].append(subject_grades)

        return grade_data
    except Enrollment.DoesNotExist:
        return None