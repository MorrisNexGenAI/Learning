import time
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, FileResponse
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from schools_templates.bomi_junior_high.utils import generate_gradesheet_pdf
from students.views import get_students_by_level, format_student_data, format_student_name
from levels.views import get_level_by_id, get_all_levels
from grades.views import get_grade_map, calc_semester_avg, calc_final_avg, save_grade
from subjects.views import get_subjects_by_level
from periods.views import get_all_periods
from enrollment.views import get_enrollment_by_student_level
from grades.models import Grade
from grades.serializers import GradeSerializer
import os
import logging

logger = logging.getLogger(__name__)

class GradeSheetViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'], url_path='by_level')
    def list_by_level(self, request):
        level_id = request.query_params.get('level_id')
        if not level_id:
            return Response({"error": "Level ID is required"}, status=status.HTTP_400_BAD_REQUEST)
  
        students = get_students_by_level(level_id)
        grade_map = get_grade_map(level_id)
        subjects_by_id = get_subjects_by_level(level_id)
        print(f"Subjects for level {level_id} (by ID): {subjects_by_id}")

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

        print(f"Queried grade map for level {level_id}: {grade_map}")
        print(f"Returning grade sheet data for level {level_id}: {result}")
        return Response(result)

    @action(detail=False, methods=['get'], url_path='gradesheet/pdf/generate')
    def generate_gradesheet_pdf(self, request):
        level_id = request.query_params.get('level_id')
        student_id = request.query_params.get('student_id')
        try:
            if not level_id:
                return Response({"error": "level_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            pdf_paths = generate_gradesheet_pdf(level_id=int(level_id), student_id=int(student_id) if student_id else None)
            if not pdf_paths:
                logger.warning(f"No PDFs generated for level_id={level_id}, student_id={student_id}")
                return Response({"error": "No PDFs generated"}, status=status.HTTP_404_NOT_FOUND)
            pdf_path = pdf_paths[0]
            logger.info(f"Generated PDF: {pdf_path}")
            view_url = f"/api/grade_sheets/gradesheet/pdf/view?level_id={level_id}"
            if student_id:
                view_url += f"&student_id={student_id}"
            return Response({"message": "PDF generated successfully", "view_url": view_url})
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='gradesheet/pdf/view')
    def view_gradesheet_pdf(self, request):
        level_id = request.query_params.get('level_id')
        student_id = request.query_params.get('student_id')
        try:
            if not level_id:
                return Response({"error": "level_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            filename = f"report_card_level_{level_id}.pdf" if not student_id else f"report_card_student_{student_id}.pdf"
            pdf_path = os.path.join(settings.BASE_DIR, "output_gradesheets", filename)
            if not os.path.exists(pdf_path):
                logger.warning(f"PDF not found: {pdf_path}")
                return Response({"error": "PDF not found"}, status=status.HTTP_404_NOT_FOUND)
            with open(pdf_path, 'rb') as f:
                response = FileResponse(f, content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="{filename}"'
                logger.info(f"Serving PDF for viewing: {pdf_path}")
                return response
        except Exception as e:
            logger.error(f"Error serving PDF: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='gradesheet/pdf')
    def generate_gradesheet_pdf_view(self, request):
        level_id = request.query_params.get('level_id')
        student_id = request.query_params.get('student_id')
        try:
            if not level_id:
                return Response({"error": "level_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            pdf_paths = generate_gradesheet_pdf(level_id=int(level_id), student_id=int(student_id) if student_id else None)
            if not pdf_paths:
                logger.warning(f"No PDFs generated for level_id={level_id}, student_id={student_id}")
                return Response({"error": "No PDFs generated"}, status=status.HTTP_404_NOT_FOUND)
            pdf_path = pdf_paths[0]
            logger.info(f"Serving PDF: {pdf_path}")
            with open(pdf_path, 'rb') as f:
                response = FileResponse(f, content_type='application/pdf')
                filename = os.path.basename(pdf_path)
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
        except Exception as e:
            logger.error(f"Error in generate_gradesheet_pdf_view: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='input', url_name='input-grades')
    def input_grades(self, request):
        level_id = request.data.get('level')
        subject_id = request.data.get('subject_id')
        period_id = request.data.get('period_id')
        grades = request.data.get('grades')

        print(f"Received data: level_id={level_id}, subject_id={subject_id}, period_id={period_id}, grades={grades}")

        if not all([level_id, subject_id, period_id]) or not isinstance(grades, list):
            response_data = {"error": "Missing or invalid required fields."}
            print(f"Returning error: {response_data}")
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        try:
            existing_grades = Grade.objects.filter(
                enrollment__level_id=level_id,
                subject_id=subject_id,
                period_id=period_id
            ).values_list('enrollment__student_id', flat=True)

            saved_grades = []
            skipped_students = []
            duplicate_students = []
            errors = []

            for grade_data in grades:
                student_id = grade_data.get('student_id')
                score = grade_data.get('score')
                if not student_id or score is None:
                    errors.append({"student_id": student_id, "error": "Missing student_id or score"})
                    continue

                enrollment = get_enrollment_by_student_level(student_id, level_id)
                if not enrollment:
                    print(f"No enrollment found for student_id={student_id}, level_id={level_id}")
                    skipped_students.append(student_id)
                    continue

                if student_id in existing_grades:
                    duplicate_students.append(student_id)
                    print(f"Duplicate grade detected for student_id={student_id}, skipping update...")
                    continue

                print(f"Attempting to save grade: student_id={student_id}, score={score}, enrollment={enrollment.id}, period_id={period_id}")
                grade, result = save_grade(enrollment, subject_id, period_id, score, request)
                if grade:
                    saved_grades.append(grade.id)
                else:
                    errors.append({"student_id": student_id, "error": result})

            response_data = {
                "message": "Grades processed.",
                "saved_grades": saved_grades,
                "skipped_students": skipped_students,
                "duplicate_students": duplicate_students,
                "errors": errors
            }
            print(f"Returning response: {response_data}")

            status_code = status.HTTP_200_OK
            if errors:
                response_data["message"] = "Some grades failed validation."
                status_code = status.HTTP_400_BAD_REQUEST
            elif saved_grades or duplicate_students:
                status_code = status.HTTP_201_CREATED

            return Response(response_data, status=status_code)

        except Exception as e:
            response_data = {"error": f"Internal server error: {str(e)}"}
            print(f"Exception occurred: {response_data}")
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='by_period_subject')
    def fetch_by_subject_and_period(self, request):
        level_id = request.query_params.get('level_id')
        subject_id = request.query_params.get('subject_id')
        period_id = request.query_params.get('period_id')

        if not all([level_id, subject_id, period_id]):
            return Response({"error": "Missing required parameters."}, status=status.HTTP_400_BAD_REQUEST)

        grades = Grade.objects.filter(
            enrollment__level_id=level_id,
            subject_id=subject_id,
            period_id=period_id
        ).select_related('enrollment__student')

        result = [
            {
                "student_id": grade.enrollment.student.id,
                "student_name": format_student_name(grade.enrollment.student),
                "score": float(grade.score) if grade.score is not None else None
            }
            for grade in grades
        ]
        return Response(result)

    @action(detail=False, methods=['get'], url_path='check_enrollment')
    def check_enrollment(self, request):
        student_id = request.query_params.get('student_id')
        level_id = request.query_params.get('level_id')
        if not all([student_id, level_id]):
            return Response({"error": "student_id and level_id are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        enrollment = get_enrollment_by_student_level(student_id, level_id)
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
    if not level_id:
        return redirect(reverse('gradesheet-home'))
    
    viewset = GradeSheetViewSet()
    factory = APIRequestFactory()
    http_request = factory.get('/api/grade_sheets/by_level/', {'level_id': level_id})
    rest_request = Request(http_request)
    
    response = viewset.list_by_level(rest_request)
    if response.status_code != 200:
        return redirect(reverse('gradesheet-home'))
    
    level = get_level_by_id(level_id)
    level_name = level.name if level else "Unknown Level"
    return render(request, 'gradesheet_view.html', {
        'gradesheet': response.data,
        'level_name': level_name,
        'level_id': level_id
    })

@csrf_exempt
def input_grades_view(request):
    if request.method == 'POST':
        level_id = request.POST.get('level_id')
        subject_id = request.POST.get('subject_id')
        period_id = request.POST.get('period_id')
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
        
        if not all([level_id, subject_id, grades]):
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
        
        saved_grades = []
        skipped_students = []
        errors = []

        for grade_data in grades:
            student_id = grade_data['student_id']
            score = grade_data['score']
            
            enrollment = get_enrollment_by_student_level(student_id, level_id)
            if not enrollment:
                skipped_students.append(student_id)
                continue
            
            grade, result = save_grade(enrollment, subject_id, period_id, score, request)
            if grade:
                saved_grades.append(grade.id)
            else:
                errors.append(f"Student ID {student_id}: {result}")
        
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
        
        logging.info(f"Successfully saved {len(saved_grades)} grades")
        messages.success(request, f"Grades saved successfully for {len(saved_grades)} students")
        return redirect(f"{reverse('gradesheet-home')}?level_id={level_id}")
    
    return redirect(reverse('gradesheet-home'))

def cors_test(request):
    response = HttpResponse("CORS Test Endpoint")
    response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
    return response