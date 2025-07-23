import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from enrollment.models import Enrollment
from students.helper import get_students_by_level, format_student_name
from levels.helper import get_level_by_id, get_all_levels
from grades.helper import get_grade_map, save_grade
from subjects.helper import get_subjects_by_level
from periods.helpers import get_all_periods
from enrollment.helper import get_enrollment_by_student_level
from grades.models import Grade
from .listLevelHelper import build_gradesheet
from academic_years.models import AcademicYear
from .utils import update_grades
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponse

logger = logging.getLogger(__name__)

class GradeSheetViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['POST'], url_path='input', url_name='input-grades')
    def input_grades(self, request):
        """POST /api/grade_sheets/input/ - Bulk grade submission."""
        level_id = request.data.get('level')
        subject_id = request.data.get('subject_id')
        period_id = request.data.get('period_id')
        grades = request.data.get('grades')
        academic_year = request.data.get('academic_year')

        logger.debug(f"Received POST data: level_id={level_id}, subject_id={subject_id}, period_id={period_id}, grades={grades}, academic_year={academic_year}")

        if not isinstance(grades, list):
            grades = []
            for key, value in request.data.items():
                if key.startswith('grades[') and value:
                    student_id = key.split('[')[1].split(']')[0]
                    grades.append({'student_id': student_id, 'score': value})

        if not all([level_id, subject_id, academic_year]) or not isinstance(grades, list):
            return Response({"error": "Missing or invalid required fields, including academic_year."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            academic_year_obj = AcademicYear.objects.get(id=academic_year)
         
            saved_grades = []
            skipped_students = []
            errors = []
            affected_student_ids = []

            for grade_data in grades:
                student_id = grade_data.get('student_id')
                score = grade_data.get('score')
                grade_period_id = grade_data.get('period_id', period_id)
                if not student_id or score is None or not grade_period_id:
                    errors.append({"student_id": student_id, "error": "Missing student_id, score, or period_id"})
                    continue

                try:
                    score = int(score)
                    if not (0 <= score <= 100):
                        errors.append({"student_id": student_id, "error": "Score must be an integer between 0 and 100"})
                        continue
                except (ValueError, TypeError):
                    errors.append({"student_id": student_id, "error": "Score must be an integer"})
                    continue

                enrollment = get_enrollment_by_student_level(student_id, level_id, academic_year_obj.id)
                if not enrollment:
                    logger.warning(f"No enrollment found for student_id={student_id}, level_id={level_id}, academic_year={academic_year}")
                    skipped_students.append(student_id)
                    continue

                grade, result = save_grade(enrollment, subject_id, grade_period_id, score, request)
                if grade:
                    saved_grades.append(grade.id)
                    affected_student_ids.append(student_id)
                    logger.info(f"Saved grade: id={grade.id}, enrollment_id={enrollment.id}, subject_id={subject_id}, period_id={grade_period_id}, score={score}")
                else:
                    errors.append({"student_id": student_id, "error": result})

            if saved_grades:
                from .models import StudentGradeSheetPDF
                StudentGradeSheetPDF.objects.filter(
                    level_id=level_id,
                    student_id__in=affected_student_ids,
                    academic_year=academic_year_obj
                ).delete()
                logger.info(f"Deleted existing PDFs for students {affected_student_ids} due to new/updated grades.")

            response_data = {
                "message": "Grades processed.",
                "saved_grades": saved_grades,
                "skipped_students": skipped_students,
                "errors": errors
            }
            status_code = status.HTTP_201_CREATED if saved_grades else status.HTTP_400_BAD_REQUEST
            if errors:
                response_data["message"] = "Some grades failed validation."
                status_code = status.HTTP_400_BAD_REQUEST
            return Response(response_data, status=status_code)

        except AcademicYear.DoesNotExist:
            logger.error(f"Invalid academic year: {academic_year}")
            return Response({"error": f"Invalid academic year: {academic_year}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in input_grades: {str(e)}")
            return Response({"error": f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'], url_path='update', url_name='update-grades')
    def update_grades(self, request):
        """POST /api/grade_sheets/update/ - Update existing grades."""
        level_id = request.data.get('level')
        subject_id = request.data.get('subject_id')
        period_id = request.data.get('period_id')
        grades = request.data.get('grades')
        academic_year = request.data.get('academic_year')

        try:
            result = update_grades(level_id, subject_id, period_id, grades, academic_year)
            return Response(result['response'], status=result['status'])
        except Exception as e:
            logger.error(f"Error in update_grades: {str(e)}")
            return Response({"error": f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'], url_path='by_level')
    def list_by_level(self, request):
        """GET /api/grade_sheets/by_level/ - Retrieve grades for a level."""
        level_id = request.query_params.get('level_id')
        academic_year = request.query_params.get('academic_year')
        if not level_id or not academic_year:
            return Response({"error": "level_id and academic_year are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = build_gradesheet(level_id, academic_year)
            return Response(result)
        except Exception as e:
            logger.error(f"Error in list_by_level: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'], url_path='by_period_subject')
    def fetch_by_subject_and_period(self, request):
        """GET /api/grade_sheets/by_period_subject/ - Retrieve grades."""
        level_id = request.query_params.get('level_id')
        subject_id = request.query_params.get('subject_id')
        period_id = request.query_params.get('period_id')
        academic_year = request.query_params.get('academic_year')

        if not all([level_id, subject_id, academic_year]):
            return Response({"error": "level_id, subject_id, and academic_year are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            academic_year_obj = AcademicYear.objects.get(name=academic_year)
            grades = Grade.objects.filter(
                enrollment__level_id=level_id,
                subject_id=subject_id,
            ).select_related('enrollment__student', 'period')
            if period_id:
                grades = grades.filter(period_id=period_id)
            grades = grades.filter(enrollment__academic_year=academic_year_obj)

            result = [
                {
                    "student_id": grade.enrollment.student.id,
                    "student_name": format_student_name(grade.enrollment.student),
                    "score": grade.score,
                    "period_id": grade.period.id
                }
                for grade in grades
            ]
            return Response(result)

        except AcademicYear.DoesNotExist:
            logger.error(f"Invalid academic year: {academic_year}")
            return Response({"error": f"Invalid academic year: {academic_year}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in fetch_by_subject_and_period: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'], url_path='check_enrollment')
    def check_enrollment(self, request):
        """GET /api/grade_sheets/check_enrollment/ - Verify enrollment."""
        student_id = request.query_params.get('student_id')
        level_id = request.query_params.get('level_id')
        academic_year = request.query_params.get('academic_year')
        if not all([student_id, level_id, academic_year]):
            return Response({"error": "student_id, level_id, and academic_year are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            academic_year_obj = AcademicYear.objects.get(name=academic_year)
            enrollment = get_enrollment_by_student_level(student_id, level_id, academic_year_obj.id)
            if not enrollment:
                return Response({"enrolled": False}, status=status.HTTP_200_OK)
            return Response({"enrolled": True, "enrollment_id": enrollment.id}, status=status.HTTP_200_OK)

        except AcademicYear.DoesNotExist:
            logger.error(f"Invalid academic year: {academic_year}")
            return Response({"error": f"Invalid academic year: {academic_year}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in check_enrollment: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def gradesheet_view(request):
    """Render grade sheet view page."""
    level_id = request.GET.get('level_id')
    academic_year = request.GET.get('academic_year')
    if not level_id or not academic_year:
        messages.error(request, "Please select a valid level and academic year")
        return redirect('gradesheet-home')

    try:
        level = get_level_by_id(level_id)
        if not level:
            messages.error(request, f"Invalid level ID: {level_id}")
            return redirect('gradesheet-home')

        gradesheet = build_gradesheet(level_id, academic_year)
        level_name = level.name
        return render(request, 'grade_sheets/gradesheet_view.html', {
            'gradesheet': gradesheet,
            'level_name': level_name,
            'selected_level_id': level_id,
            'selected_academic_year': academic_year
        })
    except Exception as e:
        logger.error(f"Error in gradesheet_view: {str(e)}")
        messages.error(request, f"Error loading grades: {str(e)}")
        return redirect('gradesheet-home')

def input_grades_view(request):
    """Handle grade input via web form."""
    if request.method == 'POST':
        level_id = request.POST.get('level_id')
        subject_id = request.POST.get('subject_id')
        period_id = request.POST.get('period_id')
        academic_year = request.POST.get('academic_year')
        grades = []

        for key, score in request.POST.items():
            if key.startswith('grades'):
                student_id = key.split('[')[1].split(']')[0]
                if score:
                    try:
                        score = int(score)
                        if not (0 <= score <= 100):
                            messages.error(request, f"Score for student ID {student_id} must be an integer between 0 and 100")
                            continue
                        grades.append({'student_id': student_id, 'score': score})
                    except ValueError:
                        messages.error(request, f"Invalid score for student ID {student_id}: must be an integer")
                        continue

        if not all([level_id, subject_id, academic_year, grades]):
            messages.error(request, "Missing required fields")
            return redirect('gradesheet-home')

        try:
            academic_year_obj = AcademicYear.objects.get(name=academic_year)
            saved_grades = []
            skipped_students = []
            errors = []
            affected_student_ids = []

            for grade_data in grades:
                student_id = grade_data['student_id']
                score = grade_data['score']
                grade_period_id = period_id

                enrollment = get_enrollment_by_student_level(student_id, level_id, academic_year_obj.id)
                if not enrollment:
                    skipped_students.append(student_id)
                    continue

                grade, result = save_grade(enrollment, subject_id, grade_period_id, score, request)
                if grade:
                    saved_grades.append(grade.id)
                    affected_student_ids.append(student_id)
                else:
                    errors.append(f"Student ID {student_id}: {result}")

            if saved_grades:
                from .models import StudentGradeSheetPDF
                StudentGradeSheetPDF.objects.filter(
                    level_id=level_id,
                    student_id__in=affected_student_ids,
                    academic_year=academic_year_obj
                ).delete()
                logger.info(f"Deleted existing PDFs for students {affected_student_ids} due to new grades.")

            if errors:
                messages.error(request, f"Some grades failed: {', '.join(errors)}")
                return redirect('gradesheet-home')

            messages.success(request, f"Grades saved successfully for {len(saved_grades)} students")
            return redirect(f"{reverse('gradesheet-home')}?level_id={level_id}&academic_year={academic_year}")

        except AcademicYear.DoesNotExist:
            messages.error(request, f"Invalid academic year: {academic_year}")
            return redirect('gradesheet-home')
        except Exception as e:
            logger.error(f"Error in input_grades_view: {str(e)}")
            messages.error(request, f"Error saving grades: {str(e)}")
            return redirect('gradesheet-home')

    return redirect('gradesheet-home')

def periodic_pdf(request):
    """Render periodic PDF page."""
    levels = get_all_levels()
    academic_years = AcademicYear.objects.all()
    selected_academic_year = request.GET.get('academic_year')
    selected_level_id = request.GET.get('level_id')
    students = []
    selected_level_name = None

    if selected_academic_year and selected_level_id:
        students = get_students_by_level(selected_level_id)
        level = get_level_by_id(selected_level_id)
        selected_level_name = level.name if level else None
        students = students.filter(enrollment__academic_year__name=selected_academic_year).distinct()

    return render(request, 'grade_sheets/periodic_pdf.html', {
        'levels': levels,
        'academic_years': academic_years,
        'students': students,
        'selected_level_id': selected_level_id,
        'selected_level_name': selected_level_name,
        'selected_academic_year': selected_academic_year
    })

def yearly_pdf(request):
    """Render yearly PDF page."""
    levels = get_all_levels()
    academic_years = AcademicYear.objects.all()
    selected_academic_year = request.GET.get('academic_year')
    selected_level_id = request.GET.get('level_id')
    students = []
    selected_level_name = None

    if selected_academic_year and selected_level_id:
        students = get_students_by_level(selected_level_id)
        level = get_level_by_id(selected_level_id)
        selected_level_name = level.name if level else None
        students = students.filter(enrollment__academic_year__name=selected_academic_year).distinct()

    return render(request, 'grade_sheets/yearly_pdf.html', {
        'levels': levels,
        'academic_years': academic_years,
        'students': students,
        'selected_level_id': selected_level_id,
        'selected_level_name': selected_level_name,
        'selected_academic_year': selected_academic_year
    })

def cors_test(request):
    """Test CORS configuration."""
    return Response({"message": "CORS test successful"}, status=status.HTTP_200_OK)

@ensure_csrf_cookie
def get_csrf_token(request):
    """GET /api/csrf/ - Sets the CSRF token cookie and returns a 200 response."""
    return HttpResponse(status=200)