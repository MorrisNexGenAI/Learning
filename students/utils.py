import logging
from students.models import Student
from enrollment.models import Enrollment
from grades.models import Grade
from academic_years.models import AcademicYear
from enrollment.helper import get_enrollment_by_student_level
from grade_sheets.models import StudentGradeSheetPDF

logger = logging.getLogger(__name__)

def edit_student(student_id, level_id, academic_year, first_name=None, last_name=None, sex=None, delete=False):
    """
    Update or delete student details and invalidate affected PDFs.
    
    Args:
        student_id: ID of the student.
        level_id: ID of the level.
        academic_year: Academic year name.
        first_name: New first name (optional).
        last_name: New last name (optional).
        sex: New sex ('M' or 'F', optional).
        delete: If True, delete the enrollment (default False).
    
    Returns:
        Dict with response message and HTTP status.
    """
    if not all([student_id, level_id, academic_year]):
        return {
            "response": {"error": "student_id, level_id, and academic_year are required"},
            "status": 400
        }

    try:
        academic_year_obj = AcademicYear.objects.get(name=academic_year)
        student = Student.objects.get(id=student_id)
        enrollment = get_enrollment_by_student_level(student_id, level_id, academic_year_obj.id)
        if not enrollment:
            return {
                "response": {"error": f"No enrollment found for student_id={student_id}, level_id={level_id}, academic_year={academic_year}"},
                "status": 400
            }

        if delete:
            Grade.objects.filter(enrollment=enrollment).delete()
            StudentGradeSheetPDF.objects.filter(
                student_id=student_id,
                level_id=level_id,
                academic_year=academic_year_obj
            ).delete()
            enrollment.delete()
            logger.info(f"Deleted enrollment and grades for student_id={student_id}, level_id={level_id}, academic_year={academic_year}")
            return {
                "response": {"message": "Student enrollment deleted successfully"},
                "status": 200
            }

        updates = {}
        if first_name:
            updates['firstName'] = first_name
        if last_name:
            updates['lastName'] = last_name
        if sex:
            updates['gender'] = sex()
            if updates['gender'] not in ['M', 'F']:
                return {
                    "response": {"error": "sex must be 'M' or 'F'"},
                    "status": 400
                }

        if updates:
            Student.objects.filter(id=student_id).update(**updates)
            StudentGradeSheetPDF.objects.filter(
                student_id=student_id,
                level_id=level_id,
                academic_year=academic_year_obj
            ).delete()
            logger.info(f"Updated student details for student_id={student_id}: {updates}")
            return {
                "response": {"message": "Student details updated successfully"},
                "status": 200
            }

        return {
            "response": {"message": "No updates provided"},
            "status": 200
        }

    except Student.DoesNotExist:
        logger.error(f"Invalid student_id: {student_id}")
        return {
            "response": {"error": f"Invalid student_id: {student_id}"},
            "status": 400
        }
    except AcademicYear.DoesNotExist:
        logger.error(f"Invalid academic year: {academic_year}")
        return {
            "response": {"error": f"Invalid academic year: {academic_year}"},
            "status": 400
        }