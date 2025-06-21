from venv import logger
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
            # Calculate averages
            try:
                # First semester average (1a)
                if all(subject_grades.get(p) != '-' for p in ['1st', '2nd', '3rd', '1exam']):
                    sem1_period_avg = (int(subject_grades['1st']) + int(subject_grades['2nd']) + int(subject_grades['3rd'])) // 3
                    subject_grades['1a'] = (sem1_period_avg + int(subject_grades['1exam'])) // 2
                else:
                    subject_grades['1a'] = '-'
                # Second semester average (2a)
                if all(subject_grades.get(p) != '-' for p in ['4th', '5th', '6th', '2exam']):
                    sem2_period_avg = (int(subject_grades['4th']) + int(subject_grades['5th']) + int(subject_grades['6th'])) // 3
                    subject_grades['2a'] = (sem2_period_avg + int(subject_grades['2exam'])) // 2
                else:
                    subject_grades['2a'] = '-'
                # Final average (f)
                if subject_grades['1a'] != '-' and subject_grades['2a'] != '-':
                    subject_grades['f'] = (int(subject_grades['1a']) + int(subject_grades['2a'])) // 2
                else:
                    subject_grades['f'] = '-'
            except (ValueError, TypeError) as e:
                logger.error(f"Error calculating averages for subject {subject.subject}: {str(e)}")
                subject_grades['1a'] = subject_grades['2a'] = subject_grades['f'] = '-'
            grade_data['s'].append(subject_grades)

        return grade_data
    except Enrollment.DoesNotExist:
        return None