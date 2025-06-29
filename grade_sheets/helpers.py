from grades.models import Grade
from subjects.models import Subject
from enrollment.models import Enrollment
from .utils import determine_pass_fail
from periods.models import Period
import logging


logger = logging.getLogger(__name__)

def get_grade_sheet_data(student_id, level_id, academic_year_id=None):
    """Compile grade data for a student, level, and optional academic year."""
    try:
        enrollment = Enrollment.objects.get(student_id=student_id, level_id=level_id, academic_year_id=academic_year_id)
        grades = Grade.objects.filter(enrollment=enrollment).select_related('subject', 'period')
        subjects = Subject.objects.filter(level_id=level_id)
        periods = Period.objects.all()
        period_map = {p.id: p.period for p in periods}
        logger.debug(f"Period map: {period_map}")

        grade_data = {
            'student_id': student_id,
            'student_name': f"{enrollment.student.firstName} {enrollment.student.lastName}",
            's': [],
            'status': determine_pass_fail(student_id, level_id, academic_year_id)
        }

        for subject in subjects:
            subject_grades = {'subject_id': str(subject.id), 'sn': subject.subject}
            for period in periods:
                grade = grades.filter(subject=subject, period=period).first()
                subject_grades[period.period] = str(grade.score) if grade and grade.score is not None else '-'
            
            # Calculate averages
            try:
                # First semester average (1a): ((1st + 2nd + 3rd) / 3 + 1exam) / 2
                sem1_grades = [subject_grades[p] for p in ['1st', '2nd', '3rd'] if subject_grades.get(p) != '-']
                exam1 = subject_grades.get('1exam', '-')
                if len(sem1_grades) == 3 and exam1 != '-':
                    sem1_period_avg = sum(int(g) for g in sem1_grades) // 3
                    subject_grades['1a'] = str((sem1_period_avg + int(exam1)) // 2)
                else:
                    subject_grades['1a'] = '-'
                    logger.debug(f"Skipping 1a for {subject_grades['sn']}: sem1_grades={sem1_grades}, exam1={exam1}")

                # Second semester average (2a): ((4th + 5th + 6th) / 3 + 2exam) / 2
                sem2_grades = [subject_grades[p] for p in ['4th', '5th', '6th'] if subject_grades.get(p) != '-']
                exam2 = subject_grades.get('2exam', '-')
                if len(sem2_grades) == 3 and exam2 != '-':
                    sem2_period_avg = sum(int(g) for g in sem2_grades) // 3
                    subject_grades['2a'] = str((sem2_period_avg + int(exam2)) // 2)
                else:
                    subject_grades['2a'] = '-'
                    logger.debug(f"Skipping 2a for {subject_grades['sn']}: sem2_grades={sem2_grades}, exam2={exam2}")

                # Final average (f): (1a + 2a) / 2
                if subject_grades['1a'] != '-' and subject_grades['2a'] != '-':
                    subject_grades['f'] = str((int(subject_grades['1a']) + int(subject_grades['2a'])) // 2)
                else:
                    subject_grades['f'] = '-'
                    logger.debug(f"Skipping f for {subject_grades['sn']}: 1a={subject_grades['1a']}, 2a={subject_grades['2a']}")

                logger.debug(f"Averages for {subject_grades['sn']}: 1a={subject_grades['1a']}, 2a={subject_grades['2a']}, f={subject_grades['f']}")
            except (ValueError, TypeError) as e:
                logger.error(f"Error calculating averages for subject {subject_grades['sn']} (student_id={student_id}): {str(e)}")
                subject_grades['1a'] = subject_grades['2a'] = subject_grades['f'] = '-'

            grade_data['s'].append(subject_grades)

        logger.info(f"Grade sheet data built for student_id={student_id}, level_id={level_id}, academic_year_id={academic_year_id}")
        return grade_data
    except Enrollment.DoesNotExist:
        logger.warning(f"No enrollment found for student_id={student_id}, level_id={level_id}, academic_year_id={academic_year_id}")
        return None
    except Exception as e:
        logger.error(f"Error in get_grade_sheet_data: {str(e)}")
        raise