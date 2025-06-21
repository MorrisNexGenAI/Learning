 @action(detail=False, methods=['GET'], url_path='gradesheet/pdf/generate')
    def generate_gradesheet_pdf(self, request):
        """GET /api/grade_sheets/gradesheet/pdf/generate/ - Generate PDFs."""
        level_id = request.query_params.get('level_id')
        student_id = request.query_params.get('student_id')
        academic_year = request.query_params.get('academic_year')
        try:
            if not level_id:
                return Response({"error": "level_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            level = get_level_by_id(level_id)
            if not level:
                return Response({"error": f"Invalid level_id: {level_id}"}, status=status.HTTP_400_BAD_REQUEST)

            student = None
            if student_id:
                student = get_students_by_level(level_id).filter(id=student_id).first()
                if not student:
                    return Response({"error": f"Invalid student_id: {student_id}"}, status=status.HTTP_400_BAD_REQUEST)

            academic_year_obj = AcademicYear.objects.get(name=academic_year) if academic_year else None
            model = StudentGradeSheetPDF if student_id else LevelGradeSheetPDF
            pdf_query = model.objects.filter(
                level_id=level_id,
                student_id=student_id if student_id else None,
                academic_year=academic_year_obj
            )
            if pdf_query.exists():
                pdf_record = pdf_query.first()
                latest_grade = Grade.objects.filter(
                    enrollment__level_id=level_id,
                    enrollment__student_id=student_id if student_id else None,
                    enrollment__academic_year=academic_year_obj
                ).order_by('-updated_at').first()
                if latest_grade and latest_grade.updated_at > pdf_record.updated_at:
                    logger.info(f"New grades detected since PDF update at {pdf_record.updated_at}. Regenerating PDF.")
                    pdf_query.delete()
                elif os.path.exists(pdf_record.pdf_path):
                    return Response({
                        "message": "PDF retrieved successfully",
                        "view_url": pdf_record.view_url,
                        "pdf_path": pdf_record.pdf_path
                    })

            # Batch process for level-wide PDFs
            batch_size = 10
            pdf_paths = []
            if not student_id:
                enrollments = Enrollment.objects.filter(level_id=level_id, academic_year=academic_year_obj)
                for i in range(0, enrollments.count(), batch_size):
                    batch = enrollments[i:i + batch_size]
                    for enrollment in batch:
                        batch_paths = generate_gradesheet_pdf(
                            level_id=int(level_id),
                            student_id=enrollment.student.id,
                            academic_year=academic_year
                        )
                        pdf_paths.extend(batch_paths)
                if pdf_paths:
                    # Generate merged level-wide PDF
                    batch_paths = generate_gradesheet_pdf(
                        level_id=int(level_id),
                        student_id=None,
                        academic_year=academic_year
                    )
                    pdf_paths.extend(batch_paths)
            else:
                pdf_paths = generate_gradesheet_pdf(
                    level_id=int(level_id),
                    student_id=int(student_id),
                    academic_year=academic_year
                )

            if not pdf_paths:
                logger.warning(f"No PDFs generated for level_id={level_id}, student_id={student_id}, academic_year={academic_year}")
                return Response({"error": "No PDFs generated"}, status=status.HTTP_404_NOT_FOUND)

            for pdf_path in pdf_paths:
                pdf_filename = os.path.basename(pdf_path)
                model.objects.update_or_create(
                    level_id=level_id,
                    student_id=student_id if student_id else None,
                    academic_year=academic_year_obj,
                    defaults={'pdf_path': pdf_path, 'filename': pdf_filename}
                )

            pdf_path = pdf_paths[0]
            view_url = f"{settings.MEDIA_URL}output_gradesheets/{pdf_filename}"
            return Response({
                "message": "PDF generated successfully",
                "view_url": view_url,
                "pdf_path": pdf_path
            })

        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
view gradesheets pdf:
    @action(detail=False, methods=['GET'], url_path='gradesheet/pdf/view')
    def view_gradesheet_pdf(self, request):
        """GET /api/grade_sheets/gradesheet/pdf/view/ - Serve PDF."""
        level_id = request.query_params.get('level_id')
        student_id = request.query_params.get('student_id')
        academic_year = request.query_params.get('academic_year')
        try:
            if not level_id:
                return Response({"error": "level_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            academic_year_obj = AcademicYear.objects.get(name=academic_year) if academic_year else None
            model = StudentGradeSheetPDF if student_id else LevelGradeSheetPDF
            pdf_query = model.objects.filter(
                level_id=level_id,
                student_id=student_id if student_id else None,
                academic_year=academic_year_obj
            )
            if not pdf_query.exists():
                logger.warning(f"No PDF record found for level_id={level_id}, student_id={student_id}, academic_year={academic_year}")
                return Response({"error": "PDF not found"}, status=status.HTTP_404_NOT_FOUND)

            pdf_record = pdf_query.first()
            pdf_path = pdf_record.pdf_path
            latest_grade = Grade.objects.filter(
                enrollment__level_id=level_id,
                enrollment__student_id=student_id if student_id else None,
                enrollment__academic_year=academic_year_obj
            ).order_by('-updated_at').first()

            if latest_grade and latest_grade.updated_at > pdf_record.updated_at:
                logger.info(f"New grades detected since PDF update at {pdf_record.updated_at}. Regenerating PDF.")
                pdf_query.delete()
                pdf_paths = generate_gradesheet_pdf(
                    level_id=int(level_id),
                    student_id=int(student_id) if student_id else None,
                    academic_year=academic_year
                )
                if not pdf_paths:
                    return Response({"error": "Failed to re-generate PDF"}, status=status.HTTP_404_NOT_FOUND)
                pdf_path = pdf_paths[0]
                pdf_filename = os.path.basename(pdf_path)
                model.objects.update_or_create(
                    level_id=level_id,
                    student_id=student_id if student_id else None,
                    academic_year=academic_year_obj,
                    defaults={'pdf_path': pdf_path, 'filename': pdf_filename}
                )

            if not os.path.exists(pdf_path):
                logger.warning(f"PDF file not found: {pdf_path}")
                pdf_paths = generate_gradesheet_pdf(
                    level_id=int(level_id),
                    student_id=int(student_id) if student_id else None,
                    academic_year=academic_year
                )
                if not pdf_paths:
                    return Response({"error": "Failed to re-generate PDF"}, status=status.HTTP_404_NOT_FOUND)
                pdf_path = pdf_paths[0]
                pdf_filename = os.path.basename(pdf_path)
                model.objects.update_or_create(
                    level_id=level_id,
                    student_id=student_id if student_id else None,
                    academic_year=academic_year_obj,
                    defaults={'pdf_path': pdf_path, 'filename': pdf_filename}
                )

            with open(pdf_path, 'rb') as f:
                response = FileResponse(f, content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="{pdf_filename}"'
                logger.info(f"Serving PDF for viewing: {pdf_path}")
                return response

        except Exception as e:
            logger.error(f"Error serving PDF: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

reportcardprintview:
class ReportCardPrintView(APIView):
    """POST /api/grade_sheets/report_card_print/ - Generate yearly report card PDFs."""
    def post(self, request):
        level_id = request.data.get("level_id")
        student_id = request.data.get("student_id")
        academic_year = request.data.get("academic_year")

        if not level_id:
            return Response({"error": "level_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            academic_year_obj = AcademicYear.objects.get(name=academic_year) if academic_year else None
            status_obj = PassFailedStatus.objects.filter(
                student_id=student_id, level_id=level_id, academic_year=academic_year_obj
            ).first() if student_id else None
            pass_template = status_obj.status in ['PASS', 'CONDITIONAL'] if status_obj else True
            pdf_paths = generate_yearly_gradesheet_pdf(
                level_id=level_id,
                student_id=student_id,
                pass_template=pass_template,
                academic_year=academic_year
            )

            if not pdf_paths:
                return Response({"error": "No PDFs generated"}, status=status.HTTP_404_NOT_FOUND)

            pdf_path = pdf_paths[0]
            pdf_filename = os.path.basename(pdf_path)
            model = StudentGradeSheetPDF if student_id else LevelGradeSheetPDF
            model.objects.update_or_create(
                level_id=level_id,
                student_id=student_id if student_id else None,
                academic_year=academic_year_obj,
                defaults={'pdf_path': pdf_path, 'filename': pdf_filename}
            )

            view_url = f"{settings.MEDIA_URL}output_gradesheets/{pdf_filename}"
            return Response({
                "message": "PDF generated successfully",
                "view_url": view_url,
                "pdf_path": pdf_path
            })

        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

this is my grade_sheets/helper.py:from venv import logger
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
        return None my gradesheets views:import logging
import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import FileResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from enrollment.models import Enrollment
from students.helper import get_students_by_level, format_student_data, format_student_name
from levels.helper import get_level_by_id, get_all_levels
from grades.helper import get_grade_map, save_grade
from subjects.helper import get_subjects_by_level
from periods.helpers import get_all_periods
from enrollment.helper import get_enrollment_by_student_level
from grades.models import Grade
from .listLevelHelper import build_gradesheet
from .models import StudentGradeSheetPDF, LevelGradeSheetPDF
from academic_years.models import AcademicYear
from pass_and_failed.models import PassFailedStatus

from .yearly_pdf_utils import generate_yearly_gradesheet_pdf
from django.urls import reverse

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
            grades=[]
            for key, value in request.data.items():
                if key.startswith('grades[') and value:
                    student_id = key.split('[')[1].split(']')[0]
                    grades.append({'student_id': student_id, 'score': value})

        if not all([level_id, subject_id, academic_year]) or not isinstance(grades, list):
            return Response({"error": "Missing or invalid required fields, including academic_year."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            academic_year_obj = AcademicYear.objects.get(id=academic_year) if academic_year else None
         
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

                # Validate score is an integer
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

        except Exception as e:
            logger.error(f"Error in input_grades: {str(e)}")
            return Response({"error": f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'], url_path='by_level')
    def list_by_level(self, request):
        """GET /api/grade_sheets/by_level/ - Retrieve grades for a level."""
        level_id = request.query_params.get('level_id')
        academic_year = request.query_params.get('academic_year')
        if not level_id:
            return Response({"error": "Level ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = build_gradesheet(level_id, academic_year)
            return Response(result)
        except Exception as e:
            logger.error(f"Error in list_by_level:{str(e)}")
            return Response({"error":str(e)}, status=status.HTTP_400_BAD_REQUEST)

       
    @action(detail=False, methods=['GET'], url_path='by_period_subject')
    def fetch_by_subject_and_period(self, request):
        """GET /api/grade_sheets/by_period_subject/ - Retrieve grades."""
        level_id = request.query_params.get('level_id')
        subject_id = request.query_params.get('subject_id')
        period_id = request.query_params.get('period_id')
        academic_year = request.query_params.get('academic_year')

        if not all([level_id, subject_id]):
            return Response({"error": "Missing required parameters."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            academic_year_obj = AcademicYear.objects.get(name=academic_year) if academic_year else None
            grades = Grade.objects.filter(
                enrollment__level_id=level_id,
                subject_id=subject_id,
            ).select_related('enrollment__student', 'period')
            if period_id:
                grades = grades.filter(period_id=period_id)
            if academic_year_obj:
                grades = grades.filter(enrollment__academic_year=academic_year_obj)

            result = [
                {
                    "student_id": grade.enrollment.student.id,
                    "student_name": format_student_name(grade.enrollment.student),
                    "score": grade.score,  # No float casting needed
                    "period_id": grade.period.id
                }
                for grade in grades
            ]
            return Response(result)

        except Exception as e:
            logger.error(f"Error in fetch_by_subject_and_period: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'], url_path='check_enrollment')
    def check_enrollment(self, request):
        """GET /api/grade_sheets/check_enrollment/ - Verify enrollment."""
        student_id = request.query_params.get('student_id')
        level_id = request.query_params.get('level_id')
        academic_year = request.query_params.get('academic_year')
        if not all([student_id, level_id]):
            return Response({"error": "student_id and level_id are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            academic_year_obj = AcademicYear.objects.get(name=academic_year) if academic_year else None
            enrollment = get_enrollment_by_student_level(student_id, level_id, academic_year_obj.id if academic_year_obj else None)
            if not enrollment:
                return Response({"enrolled": False}, status=status.HTTP_200_OK)
            return Response({"enrolled": True, "enrollment_id": enrollment.id}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in check_enrollment: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

def gradesheet_home(request):
    """Render grade input home page."""
    levels = get_all_levels()
    academic_years = AcademicYear.objects.all()

    selected_level_id = request.GET.get('level_id')
    students = []
    subjects = []
    periods = get_all_periods()
    selected_level_name = None
    selected_subject_id = request.GET.get('subject_id')
    selected_period_id = request.GET.get('period_id')
    selected_academic_year = request.GET.get('academic_year')

    if selected_level_id:
        students = get_students_by_level(selected_level_id)
        subjects = get_subjects_by_level(selected_level_id)
        level = get_level_by_id(selected_level_id)
        selected_level_name = level.name if level else None
        if selected_academic_year:
            students = students.filter(enrollment__academic_year__name=selected_academic_year).distinct()
        if selected_subject_id and selected_period_id:
            students_with_grades = Grade.objects.filter(
                enrollment__level_id=selected_level_id,
                subject_id=selected_subject_id,
                period_id=selected_period_id
            ).values_list('enrollment__student_id', flat=True)
            students = [s for s in students if s.id not in students_with_grades]

    return render(request, 'grade_sheets/gradesheet.html', {
        'levels': levels,
        'academic_years': academic_years,
        'students': students,
        'subjects': subjects,
        'periods': periods,
        'selected_level_id': selected_level_id,
        'selected_level_name': selected_level_name,
        'selected_subject_id': selected_subject_id,
        'selected_period_id': selected_period_id,
        'selected_academic_year': selected_academic_year
    })

def gradesheet_view(request):
    """Render grade sheet view page."""
    level_id = request.GET.get('level_id')
    academic_year = request.GET.get('academic_year')
    if not level_id:
        messages.error(request, "Please select a valid level")
        return redirect('gradesheet-home')

    try:
        # Validate level_id
        level = get_level_by_id(level_id)
        if not level:
            messages.error(request, f"Invalid level ID: {level_id}")
            return redirect('gradesheet-home')

        gradesheet = build_gradesheet(level_id, academic_year)
        level_name = level.name
        return render(request, 'grade_sheets/gradesheet_view.html', {
            'gradesheet': gradesheet,
            'level_name': level_name,
            'level_id': level_id,
            'academic_year': academic_year
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
                        score = int(score)  # Parse as integer
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

class ReportCardPrintView(APIView):
    """POST /api/grade_sheets/report_card_print/ - Generate yearly report card PDFs."""
    def post(self, request):
        level_id = request.data.get("level_id")
        student_id = request.data.get("student_id")
        academic_year = request.data.get("academic_year")

        if not level_id:
            return Response({"error": "level_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            academic_year_obj = AcademicYear.objects.get(name=academic_year) if academic_year else None
            status_obj = PassFailedStatus.objects.filter(
                student_id=student_id, level_id=level_id, academic_year=academic_year_obj
            ).first() if student_id else None
            pass_template = status_obj.status in ['PASS', 'CONDITIONAL'] if status_obj else True
            pdf_paths = generate_yearly_gradesheet_pdf(
                level_id=level_id,
                student_id=student_id,
                pass_template=pass_template,
                academic_year=academic_year
            )

            if not pdf_paths:
                return Response({"error": "No PDFs generated"}, status=status.HTTP_404_NOT_FOUND)

            pdf_path = pdf_paths[0]
            pdf_filename = os.path.basename(pdf_path)
            model = StudentGradeSheetPDF if student_id else LevelGradeSheetPDF
            model.objects.update_or_create(
                level_id=level_id,
                student_id=student_id if student_id else None,
                academic_year=academic_year_obj,
                defaults={'pdf_path': pdf_path, 'filename': pdf_filename}
            )

            view_url = f"{settings.MEDIA_URL}output_gradesheets/{pdf_filename}"
            return Response({
                "message": "PDF generated successfully",
                "view_url": view_url,
                "pdf_path": pdf_path
            })

        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def cors_test(request):
    """Test CORS configuration."""
    return Response({"message": "CORS test successful"}, status=status.HTTP_200_OK) but no avearages are appearing on my react fronend: my gradesheets components:
import React from 'react';
import type { Subject, Period, GradeSheet } from '../../types';

interface GradeSheetTableProps {
  gradesheets: GradeSheet[];
  subjects: Subject[];
  periods: Period[];
}

const GradeSheetTable: React.FC<GradeSheetTableProps> = ({ gradesheets, subjects }) => {
  const handlePrint = () => {
    window.print();
  };

  if (!gradesheets.length) {
    return <p>No gradesheet data available</p>;
  }

  // Use transformed subjects directly from gradesheets
  const fixedSubjects = gradesheets[0].subjects.map((s) => ({
    id: Number(s.subject_id), // Convert string to number
    name: s.subject_name,
  }));

  if (!fixedSubjects.length) {
    return <p>No subjects available for this student</p>;
  }

  return (
    <div className="b-gradesheet-table-container">
      <button className="b-print-button" onClick={handlePrint}>
        Print Grade Sheet
      </button>
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-gray-200">
            <th className="border p-2">Subjects</th>
            <th className="border p-2">1st Period</th>
            <th className="border p-2">2nd Period</th>
            <th className="border p-2">3rd Period</th>
            <th className="border p-2">1st Semester Exam</th>
            <th className="border p-2">1st Semester Avg</th>
            <th className="border p-2">4th Period</th>
            <th className="border p-2">5th Period</th>
            <th className="border p-2">6th Period</th>
            <th className="border p-2">Final Exam</th>
            <th className="border p-2">2nd Semester Avg</th>
            <th className="border p-2">Final Avg</th>
          </tr>
        </thead>
        <tbody>
          {fixedSubjects.map(({ id, name }) => {
            const subjectData = gradesheets[0].subjects.find((s) => Number(s.subject_id) === id) || {
              subject_id: id.toString(),
              subject_name: name,
              first_period: '',
              second_period: '',
              third_period: '',
              first_exam: '',
              fourth_period: '',
              fifth_period: '',
              sixth_period: '',
              second_exam: '',
              sem1_avg: '',
              sem2_avg: '',
              final_avg: '',
            };
            return (
              <tr key={id} className="border">
                <td className="p-2">{subjectData.subject_name}</td>
                <td className="p-2 text-center">{subjectData.first_period || '-'}</td>
                <td className="p-2 text-center">{subjectData.second_period || '-'}</td>
                <td className="p-2 text-center">{subjectData.third_period || '-'}</td>
                <td className="p-2 text-center">{subjectData.first_exam || '-'}</td>
                <td className="p-2 text-center">{subjectData.sem1_avg || '-'}</td>
                <td className="p-2 text-center">{subjectData.fourth_period || '-'}</td>
                <td className="p-2 text-center">{subjectData.fifth_period || '-'}</td>
                <td className="p-2 text-center">{subjectData.sixth_period || '-'}</td>
                <td className="p-2 text-center">{subjectData.second_exam || '-'}</td>
                <td className="p-2 text-center">{subjectData.sem2_avg || '-'}</td>
                <td className="p-2 text-center">{subjectData.final_avg || '-'}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default GradeSheetTable;
 averages should be automatcally calculated and populated once the requirements are met but nothing is happening:
Subjects	1st Period	2nd Period	3rd Period	1st Semester Exam	1st Semester Avg	4th Period	5th Period	6th Period	Final Exam	2nd Semester Avg	Final Avg
English	-	-	-	-	-	-	-	-	-	-	-
Mathematics	89	98	90	88	-	-	-	-	-	-	-
History	-	-	-	-	-	-	-	-	-	-	-
General Science	-	-	-	-	-	-	-	-	-	-	-
Geography	-	-	-	-	-	-	-	-	-	-	-
Civics	-	-	-	-	-	-	-	-	-	-	-
Literature	-	-	-	-	-	-	-	-	-	-	-
R.M.E	-	-	-	-	-	-	-	-	-	-	-
Agriculture	88	78	-	-	-	-	-	-	-	-	-
Vocabulary	-	-	-	-	-	-	-	-	-	-	-
Message limit reached