from academic_years.models import AcademicYear
from students.helper import get_students_by_level, format_student_data
from grades.helper import get_grade_map
from subjects.helper import get_subjects_by_level
from periods.helpers import get_all_periods
from enrollment.models import Enrollment
import logging
from .utils import determine_pass_fail

logger = logging.getLogger(__name__)

def build_gradesheet(level_id, academic_year=None):
    try:
        # Get academic year
        academic_year_obj = AcademicYear.objects.get(name=academic_year) if academic_year else None
        logger.info(f"Building gradesheet for level_id={level_id}, academic_year={academic_year}")

        # Get enrollments and students
        enrollments = Enrollment.objects.filter(level_id=level_id)
        if academic_year_obj:
            enrollments = enrollments.filter(academic_year=academic_year_obj)
        enrollment_ids = [e.id for e in enrollments]
        if not enrollment_ids:
            logger.warning(f"No enrollments found for level_id={level_id}, academic_year={academic_year}")
            return []

        students = get_students_by_level(level_id)
        if academic_year_obj:
            students = students.filter(enrollment__academic_year=academic_year_obj).distinct()
        if not students:
            logger.warning(f"No students found for level_id={level_id}, academic_year={academic_year}")
            return []

        # Get subjects and periods
        subjects_by_id = get_subjects_by_level(level_id)
        periods = get_all_periods()
        if not subjects_by_id:
            logger.warning(f"No subjects found for level_id={level_id}")
            raise ValueError("No subjects available")
        if not periods:
            logger.warning("No periods found")
            raise ValueError("No periods available")

        # Build grade_map: student_id -> subject_id -> period_key -> score
        grade_map = {student.id: {subject_id: {} for subject_id in subjects_by_id} for student in students}
        period_key_map = {p.id: p.period for p in periods}
        logger.debug(f"Period key map: {period_key_map}")

        for subject_id in subjects_by_id:
            for period in periods:
                period_key = period.period  # e.g., '1st', '2nd', '1exam'
                grades = get_grade_map(enrollment_ids, subject_id, period.id)
                logger.debug(f"Grades for subject_id={subject_id}, period={period_key}: {grades}")
                for student_id, score in grades.items():
                    if student_id in grade_map:
                        grade_map[student_id][subject_id][period_key] = score if score is not None else '-'

        # Build result
        result = []
        for student in students:
            student_data = format_student_data(student)
            student_data.update({
                "student_id": student.id,
                "student_name": f"{student.firstName} {student.lastName}",
                "status": "PENDING"
            })
            subjects_data = {
                subject_id: {
                    "subject_id": str(subject_id),
                    "subject_name": subject_name,
                    "1st": '-',
                    "2nd": '-',
                    "3rd": '-',
                    "1exam": '-',
                    "4th": '-',
                    "5th": '-',
                    "6th": '-',
                    "2exam": '-',
                    "1a": '-',
                    "2a": '-',
                    "f": '-'
                }
                for subject_id, subject_name in subjects_by_id.items()
            }

            # Populate grades
            for subject_id, grades in grade_map.get(student.id, {}).items():
                if subject_id in subjects_data:
                    subjects_data[subject_id].update({k: str(v) if v != '-' else '-' for k, v in grades.items()})

            # Calculate averages
            for subject_data in subjects_data.values():
                try:
                    # First semester average (1a): ((1st + 2nd + 3rd) / 3 + 1exam) / 2
                    sem1_grades = [subject_data[p] for p in ["1st", "2nd", "3rd"] if subject_data.get(p) != '-']
                    exam1 = subject_data.get("1exam", '-')
                    if len(sem1_grades) == 3 and exam1 != '-':
                        sem1_period_avg = sum(int(g) for g in sem1_grades) // 3
                        subject_data["1a"] = str((sem1_period_avg + int(exam1)) // 2)
                    else:
                        subject_data["1a"] = '-'
                        logger.debug(f"Skipping 1a for {subject_data['subject_name']}: sem1_grades={sem1_grades}, exam1={exam1}")

                    # Second semester average (2a): ((4th + 5th + 6th) / 3 + 2exam) / 2
                    sem2_grades = [subject_data[p] for p in ["4th", "5th", "6th"] if subject_data.get(p) != '-']
                    exam2 = subject_data.get("2exam", '-')
                    if len(sem2_grades) == 3 and exam2 != '-':
                        sem2_period_avg = sum(int(g) for g in sem2_grades) // 3
                        subject_data["2a"] = str((sem2_period_avg + int(exam2)) // 2)
                    else:
                        subject_data["2a"] = '-'
                        logger.debug(f"Skipping 2a for {subject_data['subject_name']}: sem2_grades={sem2_grades}, exam2={exam2}")

                    # Final average (f): (1a + 2a) / 2
                    if subject_data["1a"] != '-' and subject_data["2a"] != '-':
                        subject_data["f"] = str((int(subject_data["1a"]) + int(subject_data["2a"])) // 2)
                    else:
                        subject_data["f"] = '-'
                        logger.debug(f"Skipping f for {subject_data['subject_name']}: 1a={subject_data['1a']}, 2a={subject_data['2a']}")

                    logger.debug(f"Averages for {subject_data['subject_name']}: 1a={subject_data['1a']}, 2a={subject_data['2a']}, f={subject_data['f']}")
                except (ValueError, TypeError) as e:
                    logger.error(f"Error calculating averages for subject {subject_data['subject_name']} (student_id={student.id}): {str(e)}")
                    subject_data["1a"] = subject_data["2a"] = subject_data["f"] = '-'

            student_data["subjects"] = list(subjects_data.values())
            student_data["status"] = determine_pass_fail(student.id, level_id, academic_year_obj.id if academic_year_obj else None)
            result.append(student_data)

        logger.info(f"Gradesheet built for level_id={level_id}, academic_year={academic_year}, students={len(result)}")
        return result

    except AcademicYear.DoesNotExist:
        logger.error(f"Academic year {academic_year} does not exist")
        return []
    except Exception as e:
        logger.error(f"Error in build_gradesheet: {str(e)}")
        raise