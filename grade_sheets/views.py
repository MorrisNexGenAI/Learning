import logging
import os
from urllib.request import Request
from django.shortcuts import render, redirect
from django.test import RequestFactory
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponse, FileResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from students.helper import get_students_by_level, format_student_data, format_student_name
from levels.helper import get_level_by_id, get_all_levels
from grades.helper import get_grade_map, save_grade
from subjects.helper import get_subjects_by_level
from periods.helpers import get_all_periods
from enrollment.views import get_enrollment_by_student_level
from grades.models import Grade
from .models import GradeSheetPDF
from academic_years.models import AcademicYear
from pass_and_failed.models import PassFailedStatus
from .pdf_utils import generate_gradesheet_pdf
from .yearly_pdf_utils import generate_yearly_gradesheet_pdf

logger = logging.getLogger(__name__)

class GradeSheetViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['POST'], url_path='input', url_name='input-grades')
    def input_grades(self, request):
        logger.debug(f"Reached input_grades action, headers: {request.META}, data: {request.data}")
        level_id = request.data.get('level')
        subject_id = request.data.get('subject_id')
        period_id = request.data.get('period_id')
        grades = request.data.get('grades')
        academic_year = request.data.get('academic_year')

        logger.debug(f"Received POST data: level_id={level_id}, subject_id={subject_id}, period_id={period_id}, grades={grades}, academic_year={academic_year}")

        if not all([level_id, subject_id, academic_year]) or not isinstance(grades, list):
            response_data = {"error": "Missing or invalid required fields, including academic_year."}
            logger.warning(f"Returning error: {response_data}")
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        try:
            academic_year_obj = AcademicYear.objects.get(name=academic_year)
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

                enrollment = get_enrollment_by_student_level(student_id, level_id, academic_year_obj.id)
                if not enrollment:
                    logger.warning(f"No enrollment found for student_id={student_id}, level_id={level_id}, academic_year={academic_year}")
                    skipped_students.append(student_id)
                    continue

                existing_grade = Grade.objects.filter(
                    enrollment=enrollment,
                    subject_id=subject_id,
                    period_id=grade_period_id
                ).first()
                if existing_grade:
                    existing_grade.score = score
                    existing_grade.save()
                    saved_grades.append(existing_grade.id)
                    affected_student_ids.append(student_id)
                    logger.info(f"Updated grade: id={existing_grade.id}, enrollment_id={enrollment.id}, subject_id={subject_id}, period_id={grade_period_id}, score={score}")
                else:
                    grade, result = save_grade(enrollment, subject_id, grade_period_id, score, request)
                    if grade:
                        saved_grades.append(grade.id)
                        affected_student_ids.append(student_id)
                        logger.info(f"Saved grade: id={grade.id}, enrollment_id={enrollment.id}, subject_id={subject_id}, period_id={grade_period_id}, score={score}")
                    else:
                        errors.append({"student_id": student_id, "error": result})

            if saved_grades:
                GradeSheetPDF.objects.filter(
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
            logger.debug(f"Returning response: {response_data}")

            status_code = status.HTTP_200_OK
            if errors:
                response_data["message"] = "Some grades failed validation."
                status_code = status.HTTP_400_BAD_REQUEST
            elif saved_grades:
                status_code = status.HTTP_201_CREATED

            return Response(response_data, status=status_code)

        except Exception as e:
            response_data = {"error": f"Internal server error: {str(e)}"}
            logger.error(f"Exception occurred: {response_data}")
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'], url_path='by_level')
    def list_by_level(self, request):
        level_id = request.query_params.get('level_id')
        academic_year = request.query_params.get('academic_year')
        if not level_id:
            return Response({"error": "Level ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        students = get_students_by_level(level_id)
        if academic_year:
            students = students.filter(enrollment__academic_year__name=academic_year).distinct()
        grade_map = get_grade_map(level_id)
        subjects_by_id = get_subjects_by_level(level_id)
        logger.debug(f"Subjects for level {level_id} (by ID): {subjects_by_id}")

        result = []
        for student in students:
            student_data = format_student_data(student)
            subjects_data = {
                subject_id: {
                    "subject_id": subject_id,
                    "subject_name": subject_name,
                    "1st": None,
                    "2nd": None,
                    "3rd": None,
                    "1exam": None,
                    "4th": None,
                    "5th": None,
                    "6th": None,
                    "2exam": None,
                    "sem1_avg": None,
                    "sem2_avg": None,
                    "final_avg": None
                }
                for subject_id, subject_name in subjects_by_id.items()
            }

            for subject_id, grades in grade_map.get(student.id, {}).items():
                if subject_id in subjects_data:
                    subjects_data[subject_id].update(grades)

            for subject_data_item in subjects_data.values():
                period1 = subject_data_item["1st"]
                period2 = subject_data_item["2nd"]
                period3 = subject_data_item["3rd"]
                semester_exam1 = subject_data_item["1exam"]
                if all(v is not None for v in [period1, period2, period3, semester_exam1]):
                    sem1_period_avg = (period1 + period2 + period3) / 3
                    subject_data_item["sem1_avg"] = round((sem1_period_avg + semester_exam1) / 2, 1)

                period4 = subject_data_item["4th"]
                period5 = subject_data_item["5th"]
                period6 = subject_data_item["6th"]
                final_exam = subject_data_item["2exam"]
                if all(v is not None for v in [period4, period5, period6, final_exam]):
                    sem2_period_avg = (period4 + period5 + period6) / 3
                    subject_data_item["sem2_avg"] = round((sem2_period_avg + final_exam) / 2, 1)

                sem1_avg = subject_data_item["sem1_avg"]
                sem2_avg = subject_data_item["sem2_avg"]
                if sem1_avg is not None and sem2_avg is not None:
                    subject_data_item["final_avg"] = round((sem1_avg + sem2_avg) / 2, 1)

            student_data["subjects"] = list(subjects_data.values())
            result.append(student_data)

        logger.debug(f"Queried grade map for level {level_id}: {grade_map}")
        logger.debug(f"Returning grade sheet data for level {level_id}: {result}")
        return Response(result)

    @action(detail=False, methods=['GET'], url_path='gradesheet/pdf/generate')
    def generate_gradesheet_pdf(self, request):
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
                try:
                    student = get_students_by_level(level_id).filter(id=student_id).first()
                    if not student:
                        return Response({"error": f"Invalid student_id: {student_id}"}, status=status.HTTP_400_BAD_REQUEST)
                except ValueError:
                    return Response({"error": "Invalid student_id format"}, status=status.HTTP_400_BAD_REQUEST)
            
            academic_year_obj = None
            if academic_year:
                try:
                    academic_year_obj = AcademicYear.objects.get(name=academic_year)
                except AcademicYear.DoesNotExist:
                    return Response({"error": f"Invalid academic year: {academic_year}"}, status=status.HTTP_400_BAD_REQUEST)

            pdf_query = GradeSheetPDF.objects.filter(
                level_id=level_id,
                student_id=student_id if student_id else None,
                academic_year=academic_year_obj if academic_year_obj else None
            )
            if pdf_query.exists():
                pdf_record = pdf_query.first()
                latest_grade = Grade.objects.filter(
                    enrollment__level_id=level_id,
                    enrollment__student_id=student_id if student_id else None,
                    enrollment__academic_year=academic_year_obj if academic_year_obj else None
                ).order_by('-updated_at').first()
                
                if latest_grade and latest_grade.updated_at > pdf_record.updated_at:
                    logger.info(f"New grades detected since PDF update at {pdf_record.updated_at}. Regenerating PDF.")
                    pdf_query.delete()
                elif os.path.exists(pdf_record.pdf_path):
                    logger.info(f"Returning existing PDF: {pdf_record.pdf_path}")
                    return Response({
                        "message": "PDF retrieved successfully",
                        "view_url": pdf_record.view_url,
                        "pdf_path": pdf_record.pdf_path
                    })

            pdf_paths = generate_gradesheet_pdf(
                level_id=int(level_id),
                student_id=int(student_id) if student_id else None,
                academic_year=academic_year
            )
            if not pdf_paths:
                logger.warning(f"No PDFs generated for level_id={level_id}, student_id={student_id}, academic_year={academic_year}")
                return Response({"error": "No PDFs generated"}, status=status.HTTP_404_NOT_FOUND)
            
            pdf_path = pdf_paths[0]
            logger.info(f"Generated PDF: {pdf_path}")
            
            pdf_filename = os.path.basename(pdf_path)
            GradeSheetPDF.objects.update_or_create(
                level_id=level_id,
                student_id=student_id if student_id else None,
                academic_year=academic_year_obj if academic_year_obj else None,
                defaults={
                    'pdf_path': pdf_path,
                    'filename': pdf_filename,
                }
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

    @action(detail=False, methods=['GET'], url_path='gradesheet/pdf/view')
    def view_gradesheet_pdf(self, request):
        level_id = request.query_params.get('level_id')
        student_id = request.query_params.get('student_id')
        academic_year = request.query_params.get('academic_year')
        try:
            if not level_id:
                return Response({"error": "level_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            academic_year_obj = None
            if academic_year:
                try:
                    academic_year_obj = AcademicYear.objects.get(name=academic_year)
                except AcademicYear.DoesNotExist:
                    return Response({"error": f"Invalid academic year: {academic_year}"}, status=status.HTTP_400_BAD_REQUEST)

            pdf_query = GradeSheetPDF.objects.filter(
                level_id=level_id,
                student_id=student_id if student_id else None,
                academic_year=academic_year_obj if academic_year_obj else None
            )
            if not pdf_query.exists():
                logger.warning(f"No PDF record found for level_id={level_id}, student_id={student_id}, academic_year={academic_year}")
                return Response({"error": "PDF not found"}, status=status.HTTP_404_NOT_FOUND)
            
            pdf_record = pdf_query.first()
            pdf_path = pdf_record.pdf_path
            latest_grade = Grade.objects.filter(
                enrollment__level_id=level_id,
                enrollment__student_id=student_id if student_id else None,
                enrollment__academic_year=academic_year_obj if academic_year_obj else None
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
                GradeSheetPDF.objects.update_or_create(
                    level_id=level_id,
                    student_id=student_id if student_id else None,
                    academic_year=academic_year_obj if academic_year_obj else None,
                    defaults={
                        'pdf_path': pdf_path,
                        'filename': pdf_filename,
                    }
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
                pdf_record.pdf_path = pdf_path
                pdf_record.filename = os.path.basename(pdf_path)
                pdf_record.save()
            
            with open(pdf_path, 'rb') as f:
                response = FileResponse(f, content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="{pdf_record.filename}"'
                logger.info(f"Serving PDF for viewing: {pdf_path}")
                return response
        except Exception as e:
            logger.error(f"Error serving PDF: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'], url_path='by_period_subject')
    def fetch_by_subject_and_period(self, request):
        logger.debug(f"Reached fetch_by_subject_and_period action, headers: {request.META}")
        level_id = request.query_params.get('level_id')
        subject_id = request.query_params.get('subject_id')
        period_id = request.query_params.get('period_id')
        academic_year = request.query_params.get('academic_year')

        logger.debug(f"Received GET params: level_id={level_id}, subject_id={subject_id}, period_id={period_id}, academic_year={academic_year}")

        if not all([level_id, subject_id]):
            return Response({"error": "Missing required parameters."}, status=status.HTTP_400_BAD_REQUEST)

        grades = Grade.objects.filter(
            enrollment__level_id=level_id,
            subject_id=subject_id,
        )
        if period_id:
            grades = grades.filter(period_id=period_id)
        if academic_year:
            academic_year_obj = AcademicYear.objects.get(name=academic_year)
            grades = grades.filter(enrollment__academic_year=academic_year_obj)

        grades = grades.select_related('enrollment__student', 'period')

        result = [
            {
                "student_id": grade.enrollment.student.id,
                "student_name": format_student_name(grade.enrollment.student),
                "score": float(grade.score) if grade.score is not None else None,
                "period_id": grade.period.id if grade.period else None,
            }
            for grade in grades
        ]
        logger.debug(f"Returning grades: {result}")
        return Response(result)

    @action(detail=False, methods=['GET'], url_path='check_enrollment')
    def check_enrollment(self, request):
        student_id = request.query_params.get('student_id')
        level_id = request.query_params.get('level_id')
        academic_year = request.query_params.get('academic_year')
        if not all([student_id, level_id]):
            return Response({"error": "student_id and level_id are required"}, status=status.HTTP_400_BAD_REQUEST)

        academic_year_obj = AcademicYear.objects.get(name=academic_year) if academic_year else None
        enrollment = get_enrollment_by_student_level(student_id, level_id, academic_year_obj.id if academic_year_obj else None)
        if not enrollment:
            return Response({"enrolled": False}, status=status.HTTP_200_OK)
        return Response({"enrolled": True, "enrollment_id": enrollment.id}, status=status.HTTP_200_OK)

def gradesheet_home(request):
    levels = get_all_levels()
    selected_level = request.GET.get('level_id')
    students = []
    subjects = []
    periods = get_all_periods()
    selected_level_name = None
    selected_subject_id = request.GET.get('subject_id')
    selected_period_id = request.GET.get('period_id')

    if selected_level:
        students = get_students_by_level(selected_level)
        subjects = get_subjects_by_level(selected_level)
        selected_level = get_level_by_id(selected_level)
        selected_level_name = selected_level.name if selected_level else None

        if selected_subject_id and selected_period_id:
            students_with_grades = Grade.objects.filter(
                enrollment__student__level_id=selected_level,
                subject_id=selected_subject_id,
                period_id=selected_period_id
            ).values_list('enrollment__student_id', flat=True)
            students = [s for s in students if s.id not in students_with_grades]

    return render(request, 'gradesheet.html', {
        'levels': levels,
        'students': students,
        'subjects': subjects,
        'periods': periods,
        'selected_level': selected_level,
        'selected_level_name': selected_level_name,
        'selected_subject_id': selected_subject_id,
        'selected_period_id': selected_period_id,
    })

def gradesheet_view(request):
    level_id = request.GET.get('level_id')
    academic_year = request.GET.get('academic_year')
    if not level_id:
        return redirect(reverse('gradesheet-home'))

    viewset = GradeSheetViewSet()
    factory = RequestFactory()
    params = {'level_id': level_id}
    if academic_year:
        params['academic_year'] = academic_year
    http_request = factory.get('/api/grade_sheets/by_level/', params)
    rest_request = Request(http_request)

    response = viewset.list_by_level(rest_request)
    if response.status_code != 200:
        return redirect(reverse('gradesheet-home'))

    level = get_level_by_id(level_id)
    level_name = level.name if level else "Unknown Level"
    return render(request, 'gradesheet_view.html', {
        'gradesheet': response.data,
        'level_name': level_name,
        'level_id': level_id,
        'academic_year': academic_year
    })

@csrf_protect
def input_grades_view(request):
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
                        score = float(score)
                        grades.append({'student_id': student_id, 'score': score})
                    except ValueError:
                        messages.error(request, f"Invalid score for student ID {student_id}")
                        continue

        if not all([level_id, subject_id, academic_year, grades]):
            messages.error(request, "Missing required fields")
            return render(request, 'gradesheet.html', {
                'levels': get_all_levels(),
                'students': get_students_by_level(level_id),
                'subjects': get_subjects_by_level(level_id),
                'periods': get_all_periods(),
                'selected_level': level_id,
                'selected_level_name': get_level_by_id(level_id).name if get_level_by_id(level_id) else None,
                'error': "Missing required fields"
            })

        try:
            academic_year_obj = AcademicYear.objects.get(name=academic_year)
        except AcademicYear.DoesNotExist:
            messages.error(request, f"Invalid academic year: {academic_year}")
            return render(request, 'gradesheet.html', {
                'levels': get_all_levels(),
                'students': get_students_by_level(level_id),
                'subjects': get_subjects_by_level(level_id),
                'periods': get_all_periods(),
                'selected_level': level_id,
                'selected_level_name': get_level_by_id(level_id).name if get_level_by_id(level_id) else None,
                'error': f"Invalid academic year: {academic_year}"
            })

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
            GradeSheetPDF.objects.filter(
                level_id=level_id,
                student_id__in=affected_student_ids,
                academic_year=academic_year_obj
            ).delete()
            logger.info(f"Deleted existing PDFs for students {affected_student_ids} due to new grades.")

        if errors:
            messages.error(request, f"Some grades failed: {', '.join(errors)}")
            return render(request, 'gradesheet.html', {
                'levels': get_all_levels(),
                'students': get_students_by_level(level_id),
                'subjects': get_subjects_by_level(level_id),
                'periods': get_all_periods(),
                'selected_level': level_id,
                'selected_level_name': get_level_by_id(level_id).name if get_level_by_id(level_id) else None,
                'error': ", ".join(errors)
            })

        logger.info(f"Successfully saved {len(saved_grades)} grades")
        messages.success(request, f"Grades saved successfully for {len(saved_grades)} students")
        return redirect(f"{reverse('gradesheet-home')}?level_id={level_id}&academic_year={academic_year}")

    return redirect(reverse('gradesheet-home'))

class ReportCardPrintView(APIView):
    def post(self, request):
        level_id = request.data.get("level_id")
        student_id = request.data.get("student_id")
        academic_year = request.data.get("academic_year")

        if not level_id:
            return Response({"error": "level_id is required"}, status=400)

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
                return Response({"error": "No PDFs generated"}, status=404)

            pdf_path = pdf_paths[0]
            pdf_filename = os.path.basename(pdf_path)
            GradeSheetPDF.objects.update_or_create(
                level_id=level_id,
                student_id=student_id if student_id else None,
                academic_year=academic_year_obj if academic_year_obj else None,
                defaults={
                    'pdf_path': pdf_path,
                    'filename': pdf_filename,
                }
            )
            
            view_url = f"{settings.MEDIA_URL}output_gradesheets/{pdf_filename}"
            return Response({
                "message": "PDF generated successfully",
                "view_url": view_url,
                "pdf_path": pdf_path
            })

        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return Response({"error": str(e)}, status=500)

def cors_test(request):
    response = HttpResponse("CORS Test Endpoint")
    response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
    return response