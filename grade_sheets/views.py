import logging
import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import FileResponse
from django.urls import reverse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

# Model imports
from enrollment.models import Enrollment
from grades.models import Grade
from academic_years.models import AcademicYear
from pass_and_failed.models import PassFailedStatus
from .models import StudentGradeSheetPDF, LevelGradeSheetPDF

# Helper imports
from students.helper import get_students_by_level, format_student_data, format_student_name
from levels.helper import get_level_by_id, get_all_levels
from grades.helper import get_grade_map, save_grade
from subjects.helper import get_subjects_by_level
from periods.helpers import get_all_periods
from enrollment.helper import get_enrollment_by_student_level

# Utility imports
from .pdf_utils import generate_gradesheet_pdf
from .yearly_pdf_utils import generate_yearly_gradesheet_pdf

logger = logging.getLogger(__name__)


class GradeSheetViewSet(viewsets.ViewSet):
    """ViewSet for handling grade sheet operations via API endpoints."""

    @action(detail=False, methods=['POST'], url_path='input', url_name='input-grades')
    def input_grades(self, request):
        """
        POST /api/grade_sheets/input/ - Bulk grade submission.
        
        Accepts grade data for multiple students and saves them to the database.
        Validates scores and enrollment before saving.
        """
        # Extract request data
        level_id = request.data.get('level')
        subject_id = request.data.get('subject_id')
        period_id = request.data.get('period_id')
        grades = request.data.get('grades')
        academic_year = request.data.get('academic_year')

        logger.debug(f"Received POST data: level_id={level_id}, subject_id={subject_id}, "
                    f"period_id={period_id}, grades={grades}, academic_year={academic_year}")

        # Validate required fields
        if not all([level_id, subject_id, academic_year]) or not isinstance(grades, list):
            return Response(
                {"error": "Missing or invalid required fields, including academic_year."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            academic_year_obj = AcademicYear.objects.get(name=academic_year)
            saved_grades = []
            skipped_students = []
            errors = []
            affected_student_ids = []

            # Process each grade entry
            for grade_data in grades:
                student_id = grade_data.get('student_id')
                score = grade_data.get('score')
                grade_period_id = grade_data.get('period_id', period_id)
                
                # Validate grade data
                if not student_id or score is None or not grade_period_id:
                    errors.append({
                        "student_id": student_id, 
                        "error": "Missing student_id, score, or period_id"
                    })
                    continue

                # Validate and convert score to integer
                try:
                    score = int(score)
                    if not (0 <= score <= 100):
                        errors.append({
                            "student_id": student_id, 
                            "error": "Score must be an integer between 0 and 100"
                        })
                        continue
                except (ValueError, TypeError):
                    errors.append({
                        "student_id": student_id, 
                        "error": "Score must be an integer"
                    })
                    continue

                # Check enrollment
                enrollment = get_enrollment_by_student_level(student_id, level_id, academic_year_obj.id)
                if not enrollment:
                    logger.warning(f"No enrollment found for student_id={student_id}, "
                                 f"level_id={level_id}, academic_year={academic_year}")
                    skipped_students.append(student_id)
                    continue

                # Save grade
                grade, result = save_grade(enrollment, subject_id, grade_period_id, score, request)
                if grade:
                    saved_grades.append(grade.id)
                    affected_student_ids.append(student_id)
                    logger.info(f"Saved grade: id={grade.id}, enrollment_id={enrollment.id}, "
                              f"subject_id={subject_id}, period_id={grade_period_id}, score={score}")
                else:
                    errors.append({"student_id": student_id, "error": result})

            # Clean up existing PDFs for affected students
            if saved_grades:
                StudentGradeSheetPDF.objects.filter(
                    level_id=level_id,
                    student_id__in=affected_student_ids,
                    academic_year=academic_year_obj
                ).delete()
                logger.info(f"Deleted existing PDFs for students {affected_student_ids} due to new/updated grades.")

            # Prepare response
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
            return Response(
                {"error": f"Internal server error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['GET'], url_path='by_level')
    def list_by_level(self, request):
        """
        GET /api/grade_sheets/by_level/ - Retrieve grades for a level.
        
        Returns comprehensive grade data for all students in a level,
        including calculated averages and semester grades.
        """
        level_id = request.query_params.get('level_id')
        academic_year = request.query_params.get('academic_year')
        
        if not level_id:
            return Response({"error": "Level ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            academic_year_obj = AcademicYear.objects.get(name=academic_year) if academic_year else None
            students = get_students_by_level(level_id)
            
            if academic_year_obj:
                students = students.filter(enrollment__academic_year=academic_year_obj).distinct()

            # Prepare enrollment IDs for filtering grades
            enrollment_ids = students.values_list('enrollment__id', flat=True)
            subjects_by_id = get_subjects_by_level(level_id)

            # Period mapping for grade organization
            period_id_to_key = {
                9: "1", 10: "2", 11: "3", 12: "1s",
                13: "4", 14: "5", 15: "6", 16: "2s",
            }

            grade_map = {}

            # Build the grade map for all students, subjects and periods
            for subject_id in subjects_by_id.keys():
                for period_id, period_key in period_id_to_key.items():
                    grades = get_grade_map(enrollment_ids, subject_id, period_id)
                    for student_id, score in grades.items():
                        grade_map.setdefault(student_id, {}).setdefault(subject_id, {})[period_key] = score

            # Build result data
            result = []
            for student in students:
                student_data = format_student_data(student)
                
                # Initialize subjects data structure
                subjects_data = {
                    subject_id: {
                        "subject_id": subject_id,
                        "subject_name": subject_name,
                        "1": None, "2": None, "3": None, "1s": None,
                        "4": None, "5": None, "6": None, "2s": None,
                        "1a": None, "2a": None, "f": None
                    }
                    for subject_id, subject_name in subjects_by_id.items()
                }

                # Update subject grades from grade_map
                for subject_id, grades in grade_map.get(student.id, {}).items():
                    if subject_id in subjects_data:
                        subjects_data[subject_id].update(grades)

                # Calculate averages
                for subject_data in subjects_data.values():
                    # First semester average
                    if all(subject_data.get(p) is not None for p in ["1", "2", "3", "1s"]):
                        sem1_period_avg = (subject_data["1"] + subject_data["2"] + subject_data["3"]) // 3
                        subject_data["1a"] = (sem1_period_avg + subject_data["1s"]) // 2
                    
                    # Second semester average
                    if all(subject_data.get(p) is not None for p in ["4", "5", "6", "2s"]):
                        sem2_period_avg = (subject_data["4"] + subject_data["5"] + subject_data["6"]) // 3
                        subject_data["2a"] = (sem2_period_avg + subject_data["2s"]) // 2
                    
                    # Final average
                    if subject_data["1a"] is not None and subject_data["2a"] is not None:
                        subject_data["f"] = (subject_data["1a"] + subject_data["2a"]) // 2

                student_data["subjects"] = list(subjects_data.values())
                result.append(student_data)

            return Response(result)

        except Exception as e:
            logger.error(f"Error in list_by_level: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'], url_path='by_period_subject')
    def fetch_by_subject_and_period(self, request):
        """
        GET /api/grade_sheets/by_period_subject/ - Retrieve grades by subject and period.
        
        Returns grades filtered by specific subject and optionally by period.
        """
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
                    "score": grade.score,
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
        """
        GET /api/grade_sheets/check_enrollment/ - Verify student enrollment.
        
        Checks if a student is enrolled in a specific level for an academic year.
        """
        student_id = request.query_params.get('student_id')
        level_id = request.query_params.get('level_id')
        academic_year = request.query_params.get('academic_year')
        
        if not all([student_id, level_id]):
            return Response(
                {"error": "student_id and level_id are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            academic_year_obj = AcademicYear.objects.get(name=academic_year) if academic_year else None
            enrollment = get_enrollment_by_student_level(
                student_id, level_id, 
                academic_year_obj.id if academic_year_obj else None
            )
            
            if not enrollment:
                return Response({"enrolled": False}, status=status.HTTP_200_OK)
            
            return Response(
                {"enrolled": True, "enrollment_id": enrollment.id}, 
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error in check_enrollment: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'], url_path='gradesheet/pdf/generate')
    def generate_gradesheet_pdf(self, request):
        """
        GET /api/grade_sheets/gradesheet/pdf/generate/ - Generate PDF grade sheets.
        
        Generates PDF grade sheets for individual students or entire levels.
        Handles caching and regeneration based on grade updates.
        """
        level_id = request.query_params.get('level_id')
        student_id = request.query_params.get('student_id')
        academic_year = request.query_params.get('academic_year')
        
        try:
            if not level_id:
                return Response({"error": "level_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate level
            level = get_level_by_id(level_id)
            if not level:
                return Response(
                    {"error": f"Invalid level_id: {level_id}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate student if provided
            student = None
            if student_id:
                student = get_students_by_level(level_id).filter(id=student_id).first()
                if not student:
                    return Response(
                        {"error": f"Invalid student_id: {student_id}"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            academic_year_obj = AcademicYear.objects.get(name=academic_year) if academic_year else None
            model = StudentGradeSheetPDF if student_id else LevelGradeSheetPDF
            
            # Check for existing PDF
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
                
                # Check if PDF needs regeneration
                if latest_grade and latest_grade.updated_at > pdf_record.updated_at:
                    logger.info(f"New grades detected since PDF update at {pdf_record.updated_at}. Regenerating PDF.")
                    pdf_query.delete()
                elif os.path.exists(pdf_record.pdf_path):
                    return Response({
                        "message": "PDF retrieved successfully",
                        "view_url": pdf_record.view_url,
                        "pdf_path": pdf_record.pdf_path
                    })

            # Generate new PDFs
            batch_size = 10
            pdf_paths = []
            
            if not student_id:
                # Batch process for level-wide PDFs
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
                logger.warning(f"No PDFs generated for level_id={level_id}, "
                             f"student_id={student_id}, academic_year={academic_year}")
                return Response({"error": "No PDFs generated"}, status=status.HTTP_404_NOT_FOUND)

            # Save PDF records
            for pdf_path in pdf_paths:
                pdf_filename = os.path.basename(pdf_path)
                model.objects.update_or_create(
                    level_id=level_id,
                    student_id=student_id if student_id else None,
                    academic_year=academic_year_obj,
                    defaults={'pdf_path': pdf_path, 'filename': pdf_filename}
                )

            pdf_path = pdf_paths[0]
            pdf_filename = os.path.basename(pdf_path)
            view_url = f"{settings.MEDIA_URL}output_gradesheets/{pdf_filename}"
            
            return Response({
                "message": "PDF generated successfully",
                "view_url": view_url,
                "pdf_path": pdf_path
            })

        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'], url_path='gradesheet/pdf/view')
    def view_gradesheet_pdf(self, request):
        """
        GET /api/grade_sheets/gradesheet/pdf/view/ - Serve PDF files.
        
        Serves existing PDF files or regenerates them if needed.
        Handles file existence checks and automatic regeneration.
        """
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
                logger.warning(f"No PDF record found for level_id={level_id}, "
                             f"student_id={student_id}, academic_year={academic_year}")
                return Response({"error": "PDF not found"}, status=status.HTTP_404_NOT_FOUND)

            pdf_record = pdf_query.first()
            pdf_path = pdf_record.pdf_path
            
            # Check for newer grades
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

            # Check file existence
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

            # Serve the PDF file
            with open(pdf_path, 'rb') as f:
                response = FileResponse(f, content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="{os.path.basename(pdf_path)}"'
                logger.info(f"Serving PDF for viewing: {pdf_path}")
                return response

        except Exception as e:
            logger.error(f"Error serving PDF: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportCardPrintView(APIView):
    """API view for generating yearly report card PDFs."""

    def post(self, request):
        """
        POST /api/grade_sheets/report_card_print/ - Generate yearly report card PDFs.
        
        Generates comprehensive yearly report cards with pass/fail status consideration.
        """
        level_id = request.data.get("level_id")
        student_id = request.data.get("student_id")
        academic_year = request.data.get("academic_year")

        if not level_id:
            return Response({"error": "level_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            academic_year_obj = AcademicYear.objects.get(name=academic_year) if academic_year else None
            
            # Determine pass/fail status for template selection
            status_obj = PassFailedStatus.objects.filter(
                student_id=student_id,
                level_id=level_id,
                academic_year=academic_year_obj
            ).first() if student_id else None
            
            pass_template = status_obj.status in ['PASS', 'CONDITIONAL'] if status_obj else True
            
            # Generate PDF
            pdf_paths = generate_yearly_gradesheet_pdf(
                level_id=level_id,
                student_id=student_id,
                pass_template=pass_template,
                academic_year=academic_year
            )

            if not pdf_paths:
                return Response({"error": "No PDFs generated"}, status=status.HTTP_404_NOT_FOUND)

            # Save PDF record
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


# Template Views
def gradesheet_home(request):
    """
    Render grade input home page.
    
    Provides interface for selecting levels, subjects, periods, and academic years
    for grade input operations.
    """
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
        
        # Filter by academic year
        if selected_academic_year:
            students = students.filter(enrollment__academic_year__name=selected_academic_year).distinct()
        
        # Filter out students who already have grades for the selected subject and period
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
    """
    Render grade sheet view page.
    
    Displays comprehensive grade sheets for a specific level,
    showing all students and their grades across subjects.
    """
    level_id = request.GET.get('level_id')
    academic_year = request.GET.get('academic_year')
    
    if not level_id:
        return redirect('gradesheet-home')

    try:
        viewset = GradeSheetViewSet()
        response = viewset.list_by_level(request)
        
        if response.status_code != 200:
            messages.error(request, response.data.get('error', 'Failed to load grades'))
            return redirect('gradesheet-home')

        level = get_level_by_id(level_id)
        level_name = level.name if level else "Unknown Level"
        
        return render(request, 'grade_sheets/gradesheet_view.html', {
            'gradesheet': response.data,
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
    return Response({"message": "CORS test successful"}, status=status.HTTP_200_OK)