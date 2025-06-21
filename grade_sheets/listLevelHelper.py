from academic_years.models import AcademicYear
from students.helper import get_students_by_level, format_student_data
from grades.helper import get_grade_map  # Correct import
from subjects.helper import get_subjects_by_level
from periods.helpers import get_all_periods
from enrollment.models import Enrollment

import logging

logger = logging.getLogger(__name__)

def build_gradesheet(level_id, academic_year=None):
    try:
        # Get academic year
        academic_year_obj = AcademicYear.objects.get(name=academic_year) if academic_year else None

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
        period_key_map = {p.id: p.period for p in periods}  # Map period IDs to names (e.g., 1, 2, 3, 1s, etc.)

        for subject_id in subjects_by_id:
            for period in periods:
                period_key = period.period  # Assumes period.name is '1', '2', '3', '1s', etc.
                grades = get_grade_map(enrollment_ids, subject_id, period.id)
                for student_id, score in grades.items():
                    if student_id in grade_map:
                        grade_map[student_id][subject_id][period_key] = score

        # Build result
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

            # Populate grades
            for subject_id, grades in grade_map.get(student.id, {}).items():
                if subject_id in subjects_data:
                    subjects_data[subject_id].update(grades)

            # Calculate averages
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

    except AcademicYear.DoesNotExist:
        logger.error(f"Academic year {academic_year} does not exist")
        return []
    except Exception as e:
        logger.error(f"Error in build_gradesheet: {str(e)}")
        raise