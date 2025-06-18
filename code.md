each have it own files:models, views, serializers.
# enrollment/models.py
from django.db import models
from academic_years.models import AcademicYear
from students.models import Student
from levels.models import Level
import datetime


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('pass', 'Pass'),
        ('failed', 'Failed'),
        ('conditional', 'Pass Under Condition'),
        ('none', 'None'),
    ]
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name="enrollment")
    level = models.ForeignKey('levels.Level', on_delete=models.CASCADE)
    academic_year = models.ForeignKey('academic_years.AcademicYear', on_delete=models.CASCADE)
    date_enrolled = models.DateField()
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='none')

    class Meta:
        unique_together = ('student', 'level')

    def __str__(self):
        return f"{self.student} - {self.academic_year}"

from rest_framework import serializers
from .models import Enrollment
from students.serializers import StudentSerializer
from levels.serializers import LevelSerializer
from academic_years.serializers import AcademicYearSerializer  # Adjust path

class EnrollmentSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    level = LevelSerializer(read_only=True)
    academic_year = AcademicYearSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'level', 'academic_year', 'date_enrolled']

from rest_framework import viewsets
from enrollment.models import Enrollment
from enrollment.serializers import EnrollmentSerializer

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer

def get_enrollment_by_student_level(student_id, level_id, academic_year_id=None):
    """Fetch enrollment by student, level, and optional academic year."""
    try:
        query = Enrollment.objects.filter(student_id=student_id, level_id=level_id)
        if academic_year_id:
            query = query.filter(academic_year_id=academic_year_id)
        return query.get()
    except Enrollment.DoesNotExist:
        return None

i love your observation. the status is indeed a mistake but we will chose to keep it either in enrollment because that is when a student is enroll or pass_and_failed. but could you do the enrollment over, it is too long. i need it like a readme.md or in that form. no needs for codes, just describe it. also after the explanation, just include the weakness of each django app, include it within the description you are sending so that we can work on it after this process. i don't want you hilighting it outside the expaination. you can include it like pros and cons and then we move to the next app. next is grades.
# grades/models.py
from django.db import models
from enrollment.models import Enrollment
from subjects.models import Subject
from periods.models import Period

class Grade(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    score = models.FloatField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('enrollment', 'subject', 'period')

    def __str__(self):
        return f"{self.enrollment.student} - {self.subject.subject} - {self.period.period} - {self.score}"

# grades/serializers.py
from rest_framework import serializers
from grades.models import Grade

class GradeSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(source='enrollment.student.id', read_only=True)
    student_name = serializers.CharField(source='enrollment.student.__str__', read_only=True)
    score = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)

    def validate_score(self, value):
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Score must be between 0 and 100.")
        return value

    class Meta:
        model = Grade
        fields = ['student_id', 'student_name', 'score', 'enrollment', 'subject', 'period']

import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from grades.models import Grade
from grades.serializers import GradeSerializer
from .helper import save_grade, get_grade_map

logger = logging.getLogger(__name__)

class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        student_id = self.request.query_params.get('student_id')
        subject_id = self.request.query_params.get('subject_id')
        period_id = self.request.query_params.get('period_id')

        if student_id:
            queryset = queryset.filter(enrollment__student_id=student_id)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if period_id:
            queryset = queryset.filter(period_id=period_id)

        return queryset

    def create(self, request, *args, **kwargs):
        if isinstance(request.data, list):
            serializer = self.get_serializer(data=request.data, many=True)
            if serializer.is_valid():
                self.perform_create(serializer)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from grades.models import Grade
from subjects.models import Subject
from periods.models import Period
from django.core.exceptions import ValidationError
from enrollment.models import Enrollment
import logging

logger = logging.getLogger(__name__)

def get_grade_map(level_id):
    grades = Grade.objects.filter(enrollment__level_id=level_id).select_related('enrollment__student', 'subject', 'period')
    grade_map = {}

    for grade in grades:
        student_id = grade.enrollment.student_id
        subject_id = grade.subject_id
        period = grade.period.period.lower()

        if period in ["1st semester exam", "first semester exam"]:
            period = "1exam"
        elif period in ["2nd semester exam", "second semester exam"]:
            period = "2exam"
        elif period in ["1st", "2nd", "3rd", "4th", "5th", "6th"]:
            period = period

        score = float(grade.score) if grade.score is not None else None

        if student_id not in grade_map:
            grade_map[student_id] = {}
        if subject_id not in grade_map[student_id]:
            grade_map[student_id][subject_id] = {}

        grade_map[student_id][subject_id][period] = score

    return grade_map

def calc_semester_avg(scores, exam):
    if not scores or exam is None:
        return None
    total = sum(scores)
    count = len(scores)
    total += exam
    count += 1
    return round(total / count, 2) if count > 0 else None

def calc_final_avg(sem1_avg, sem2_avg):
    if sem1_avg is None or sem2_avg is None:
        return None
    return round((sem1_avg + sem2_avg) / 2, 2)

def save_grade(enrollment: Enrollment, subject_id: int, period_id: int, score: float, request=None) -> tuple:
    if not period_id:
        logger.error(f"Period ID is null for enrollment_id={enrollment.id}, subject_id={subject_id}")
        return None, {"period": ["This field may not be null."]}

    try:
        period = Period.objects.get(id=period_id)
    except Period.DoesNotExist:
        logger.error(f"Invalid period_id={period_id}")
        return None, {"period_id": ["Invalid period ID."]}

    try:
        subject = Subject.objects.get(id=subject_id)
    except Subject.DoesNotExist:
        logger.error(f"Invalid subject_id={subject_id}")
        return None, {"subject_id": ["Invalid subject ID."]}

    try:
        if not (0 <= score <= 100):
            logger.error(f"Invalid score={score} for enrollment_id={enrollment.id}, subject_id={subject_id}, period_id={period_id}")
            return None, {"score": ["Score must be between 0 and 100."]}

        grade, created = Grade.objects.update_or_create(
            enrollment=enrollment,
            subject=subject,
            period=period,
            defaults={'score': score}
        )
        logger.info(f"{'Saved' if created else 'Updated'} grade: id={grade.id}, enrollment_id={enrollment.id}, subject_id={subject.id}, period_id={period.id}, score={score}")
        return grade, None

    except ValidationError as e:
        logger.error(f"Validation error saving grade: {str(e)}")
        return None, {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error saving grade: {str(e)}")
        return None, str(e)
i'm satisfy with it, lets move to grade_sheets:
# grade_sheets/models.py
from django.conf import settings
from django.db import models
from levels.models import Level
from students.models import Student
from academic_years.models import AcademicYear

class GradeSheetPDF(models.Model):
    pdf_path = models.CharField(max_length=512, unique=True)  # Full filesystem path
    filename = models.CharField(max_length=255)  # e.g., report_card_Jenneh_Fully_20250613_085600.pdf
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, null=True, blank=True, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('level', 'student', 'academic_year')  # Ensure one PDF per combination

    @property
    def view_url(self):
        return f"{settings.MEDIA_URL}output_gradesheets/{self.filename}"

from rest_framework import serializers
from .models import GradeSheetPDF

class GradeSheetserializer(serializers.ModelSerializer):
    class Meta:
        model = GradeSheetPDF
        fields = '__all__'

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

utils:import os
import logging
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg
from grades.models import Grade
from subjects.models import Subject
from .models import GradeSheetPDF

logger = logging.getLogger(__name__)

def cleanup_old_pdfs(days=2):
    """
    Delete PDF files and their database records older than the specified number of days.
    
    Args:
        days (int): Number of days to consider for cleanup. Defaults to 2.
    """
    cutoff = timezone.now() - timedelta(days=days)
    old_pdfs = GradeSheetPDF.objects.filter(updated_at__lt=cutoff)
    for pdf_record in old_pdfs:
        if os.path.exists(pdf_record.pdf_path):
            try:
                os.remove(pdf_record.pdf_path)
                logger.info(f"Deleted old PDF: {pdf_record.pdf_path}")
            except Exception as e:
                logger.error(f"Failed to delete PDF {pdf_record.pdf_path}: {str(e)}")
        pdf_record.delete()

def determine_pass_fail(student_id, level_id, academic_year=None, passing_score=50):
    """
    Determine pass/fail/incomplete status for a student given level and academic year.
    Conditions:
    - All subjects must have at least 8 grades recorded.
    - Average score per subject must be >= passing_score.
    - If any subject has < 8 grades or no grades, status = INCOMPLETE.
    - If any subject average < passing_score, status = FAILED.
    - Otherwise, status = PASSED.
    """
    try:
        # Get all subjects for the level
        subjects = Subject.objects.filter(level_id=level_id)
        if not subjects.exists():
            logger.warning(f"No subjects found for level {level_id}")
            return "INCOMPLETE"

        for subject in subjects:
            # Filter grades for this student, subject, level, and optionally academic year
            grade_query = Grade.objects.filter(
                enrollment__student_id=student_id,
                subject=subject,
                enrollment__level_id=level_id
            )
            if academic_year:
                grade_query = grade_query.filter(enrollment__academic_year__name=academic_year)

            grade_count = grade_query.count()
            if grade_count < 8:
                logger.debug(f"Subject {subject.subject} has incomplete grades ({grade_count} < 8)")
                return "INCOMPLETE"

            avg_score = grade_query.aggregate(avg=Avg('score'))['avg']
            if avg_score is None:
                logger.debug(f"Subject {subject.subject} has no scores recorded")
                return "INCOMPLETE"
            if avg_score < passing_score:
                logger.debug(f"Subject {subject.subject} failed with avg score {avg_score}")
                return "FAILED"

        logger.info(f"Student {student_id} passed level {level_id} for year {academic_year}")
        return "PASSED"

    except Exception as e:
        logger.error(f"Error determining pass/fail for student {student_id}: {str(e)}")
        return "INCOMPLETE"

pdf_utils:import os
import time
import logging
import pythoncom
from django.conf import settings
from docxtpl import DocxTemplate
from docx2pdf import convert
from PyPDF2 import PdfMerger
from grade_sheets.helpers import get_grade_sheet_data
from students.models import Student
from enrollment.models import Enrollment

logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(settings.MEDIA_ROOT, "output_gradesheets")
TEMPLATE_PATH = os.path.join(settings.MEDIA_ROOT, "templates", "report_card_compact.docx")

def generate_gradesheet_pdf(level_id, student_id=None, academic_year=None):
    """
    Generate individual report card PDFs using report_card_compact.docx for students in the given level_id or a single student_id.
    Returns a list of generated PDF paths or a single merged PDF path for bulk printing.
    """
    try:
        logger.debug(f"Starting PDF generation for level_id={level_id}, student_id={student_id}, academic_year={academic_year}")
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            logger.info(f"Created output directory: {OUTPUT_DIR}")

        if not os.access(OUTPUT_DIR, os.W_OK):
            raise PermissionError(f"No write permission for {OUTPUT_DIR}")

        if not os.path.exists(TEMPLATE_PATH):
            raise FileNotFoundError(f"Template not found at {TEMPLATE_PATH}")
        logger.info(f"Using template: {TEMPLATE_PATH}")

        pdf_paths = []
        if student_id:
            student = Student.objects.get(id=student_id)
            enrollments = Enrollment.objects.filter(student_id=student_id, level_id=level_id)
            if academic_year:
                enrollments = enrollments.filter(academic_year__name=academic_year)
            students = [student] if enrollments.exists() else []
        else:
            enrollments = Enrollment.objects.filter(level_id=level_id).select_related("student")
            if academic_year:
                enrollments = enrollments.filter(academic_year__name=academic_year)
            students = [enrollment.student for enrollment in enrollments]

        if not students:
            logger.warning(f"No students found for level_id: {level_id}, student_id: {student_id}, academic_year:{academic_year}")
            return pdf_paths

        for student in students:
            logger.debug(f"Processing student: {student.id}")
            student_data = get_grade_sheet_data(student.id, level_id, academic_year)
            logger.info(f"Prepared data for student: {student_data['name']}")

            student_name = student_data["name"].replace(" ", "_")
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            docx_path = os.path.join(OUTPUT_DIR, f"report_card_{student_name}_{timestamp}.docx")
            pdf_path = os.path.join(OUTPUT_DIR, f"report_card_{student_name}_{timestamp}.pdf")
            logger.debug(f"Output paths: docx={docx_path}, pdf={pdf_path}")

            if os.path.exists(docx_path) and not os.access(docx_path, os.W_OK):
                raise PermissionError(f"No write permission for {docx_path}")

            logger.debug("Rendering template")
            template = DocxTemplate(TEMPLATE_PATH)
            template.render(student_data)
            template.save(docx_path)
            logger.info(f"Saved .docx: {docx_path}")

            if not os.path.exists(docx_path):
                raise FileNotFoundError(f"Failed to create .docx at {docx_path}")
            if os.path.getsize(docx_path) == 0:
                raise ValueError(f"Generated .docx is empty: {docx_path}")

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    pythoncom.CoInitialize()
                    logger.debug(f"Attempt {attempt + 1}: Converting {docx_path} to {pdf_path}")
                    convert(docx_path, pdf_path)
                    logger.info(f"Converted to PDF: {pdf_path}")
                    break
                except Exception as e:
                    logger.error(f"PDF conversion attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        raise Exception(f"PDF conversion failed after {max_retries} attempts: {str(e)}")
                    time.sleep(2)
                finally:
                    pythoncom.CoUninitialize()

            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF generation failed for {pdf_path}")
            if os.path.getsize(pdf_path) == 0:
                raise ValueError(f"Generated PDF is empty: {pdf_path}")

            try:
                os.remove(docx_path)
                logger.info(f"Cleaned up .docx: {docx_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up .docx: {str(e)}")

            pdf_paths.append(pdf_path)

        if not student_id and pdf_paths:
            merged_pdf_path = os.path.join(OUTPUT_DIR, f"report_cards_level_{level_id}_{timestamp}.pdf")
            merger = PdfMerger()
            for pdf_path in pdf_paths:
                merger.append(pdf_path)
            merger.write(merged_pdf_path)
            merger.close()
            logger.info(f"Merged PDFs into: {merged_pdf_path}")

            if not os.path.exists(merged_pdf_path):
                raise FileNotFoundError(f"Merged PDF not created: {merged_pdf_path}")
            if os.path.getsize(merged_pdf_path) == 0:
                raise ValueError(f"Merged PDF is empty: {merged_pdf_path}")

            for pdf_path in pdf_paths:
                try:
                    os.remove(pdf_path)
                    logger.info(f"Cleaned up individual PDF: {pdf_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up PDF: {str(e)}")

            return [merged_pdf_path]

        return pdf_paths

    except Exception as e:
        logger.error(f"Error generating gradesheet PDF: {str(e)}")
        raise Exception(f"Error generating gradesheet PDF: {str(e)}")

helper:
from django.db.models import Q
from students.models import Student
from subjects.models import Subject
from grades.models import Grade
from enrollment.models import Enrollment
import logging

# Import the new pass/fail utility function
from .utils import determine_pass_fail

logger = logging.getLogger(__name__)

def get_grade_sheet_data(student_id, level_id, academic_year=None):
    logger.debug(f"Fetching grade sheet data for student_id={student_id}, level_id={level_id}, academic_year={academic_year}")
    try:
        student = Student.objects.get(id=student_id)
        subjects = Subject.objects.filter(level_id=level_id)
        
        # Filter grades by enrollment, level, and academic year
        grade_query = Grade.objects.filter(
            Q(enrollment__student__id=student_id) & 
            Q(subject__level_id=level_id)
        )
        
        if academic_year:
            grade_query = grade_query.filter(enrollment__academic_year__name=academic_year)
        
        grades = grade_query.select_related('subject', 'enrollment', 'period')

        logger.debug(f"Raw grades query for level {level_id}: {list(grades)}")

        subject_data = []
        for subject in subjects:
            subject_grades = {}
            for grade in grades.filter(subject_id=subject.id):
                logger.debug(f"Mapping grade: enrollment_id={grade.enrollment_id}, subject_id={grade.subject_id}, period={grade.period.period}, score={grade.score}")
                period_map = {
                    '1st': '1',
                    '2nd': '2',
                    '3rd': '3',
                    '1exam': '1s',
                    '4th': '4',
                    '5th': '5',
                    '6th': '6',
                    '2exam': '2s'
                }
                subject_grades[period_map.get(grade.period.period, grade.period.period)] = float(grade.score) if grade.score is not None else '-'

            data = {
                "id": subject.id,
                "sn": subject.subject,
                "1": subject_grades.get("1", ""),
                "2": subject_grades.get("2", ""),
                "3": subject_grades.get("3", ""),
                "1s": subject_grades.get("1s", ""),
                "4": subject_grades.get("4", ""),
                "5": subject_grades.get("5", ""),
                "6": subject_grades.get("6", ""),
                "2s": subject_grades.get("2s", ""),
                "1a": "",
                "2a": "",
                "f": ""
            }
            subject_data.append(data)

        # Call the pass/fail function and add to the returned data
        status = determine_pass_fail(student_id, level_id, academic_year)

        grade_sheet_data = {
            "name": f"{student.firstName} {student.lastName}",
            "s": subject_data,
            "status": status,  # added pass/fail status here
        }
        logger.info(f"Grade sheet data for student {student_id}, level {level_id}: {grade_sheet_data}")
        return grade_sheet_data
    except Exception as e:
        logger.error(f"Error generating grade sheet data: {str(e)}")
        raise

i'm satisfy. next is students.
from django.db import models
from academic_years.models import AcademicYear
from levels.models import Level

# Create your models here.
class Student(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
   
    firstName = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50)
    gender = models.CharField(max_length =1,choices=GENDER_CHOICES)
    dob = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
   
   
   
    def __str__(self):
        return f"{self.firstName} {self.lastName}"


from rest_framework import serializers
from students.models import Student
from levels.models import Level
from enrollment.models import Enrollment
from levels.serializers import LevelSerializer
from academic_years.models import AcademicYear

class StudentSerializer(serializers.ModelSerializer):
    level = serializers.SerializerMethodField()
    academic_year = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ['id', 'firstName', 'lastName', 'gender', 'dob', 'level', 'academic_year']

    def get_level(self, obj):
        enrollment = obj.enrollment.first()
        if enrollment and enrollment.level:
            return LevelSerializer(enrollment.level).data
        return None

    def get_academic_year(self, obj):
        enrollment = obj.enrollment.first()
        if enrollment and enrollment.academic_year:
            return {'id': enrollment.academic_year.id, 'name': enrollment.academic_year.name}
        return None

    def create(self, validated_data):
        student = Student.objects.create(**validated_data)
        return student  # Enrollment will be handled in ViewSet

import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Student
from .serializers import StudentSerializer
from levels.models import Level
from academic_years.models import AcademicYear

from .helper import (
    create_enrollment_for_student,
    create_pass_failed_status,
)

logger = logging.getLogger(__name__)

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            student = serializer.save()
            logger.info(f"Created student: {student.id} - {student.firstName} {student.lastName}")

            level_id = request.data.get('level')
            academic_year_id = request.data.get('academic_year')

            if not level_id or not academic_year_id:
                return Response({
                    "student": serializer.data,
                    "warning": "Student created but not enrolled due to missing level or academic_year"
                }, status=status.HTTP_201_CREATED)

            try:
                level = Level.objects.get(id=level_id)
                academic_year = AcademicYear.objects.get(id=academic_year_id)

                enrollment = create_enrollment_for_student(student, level, academic_year)
                create_pass_failed_status(student, level, academic_year, enrollment)

            except Exception as e:
                logger.error(f"Post-creation error: {str(e)}")
                return Response({
                    "student": serializer.data,
                    "error": f"Created but enrollment/pass_failed failed: {str(e)}"
                }, status=status.HTTP_201_CREATED)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating student: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        queryset = Student.objects.all()
        level_id = self.request.query_params.get('level_id')
        academic_year_name = self.request.query_params.get('academic_year')

        if level_id and academic_year_name:
            try:
                level = Level.objects.get(id=level_id)
                academic_year = AcademicYear.objects.get(name=academic_year_name)
                queryset = queryset.filter(
                    enrollment__level=level,
                    enrollment__academic_year=academic_year
                )
            except (Level.DoesNotExist, AcademicYear.DoesNotExist):
                return Student.objects.none()

        return queryset

helper:
from .models import Student
from enrollment.models import Enrollment
from pass_and_failed.models import PassFailedStatus
from grades.models import Grade
from subjects.models import Subject

def get_students_by_level(level_id):
    """Fetch students by level ID."""
    return Student.objects.filter(enrollment__level_id=level_id).distinct()

def format_student_data(student):
    """Format student data for use in grade sheets."""
    return {
        "student_id": student.id,
        "student_name": f"{student.firstName} {student.lastName}",
        "subjects": []  # To be populated externally
    }

def format_student_name(student):
    """Format student full name."""
    return f"{student.firstName} {student.lastName}"

def create_enrollment_for_student(student, level, academic_year):
    """Create an enrollment record."""
    return Enrollment.objects.create(
        student=student,
        level=level,
        academic_year=academic_year
    )

def create_pass_failed_status(student, level, academic_year, enrollment):
    """Auto-create pass/fail status for a student."""
    grades = Grade.objects.filter(enrollment=enrollment)
    subject_count = Subject.objects.filter(level=level).count()
    expected_grades = subject_count * 8 if subject_count else 1
    grades_complete = grades.exists()
    status_value = 'INCOMPLETE' if grades.count() < expected_grades else 'PENDING'

    return PassFailedStatus.objects.create(
        student=student,
        level=level,
        academic_year=academic_year,
        enrollment=enrollment,
        grades_complete=grades_complete,
        status=status_value,
        template_name='pass_template.html'
    )

api:from django.urls import path
from rest_framework.routers import DefaultRouter
from students.views import StudentViewSet
from levels.views import LevelViewSet
from grades.views import GradeViewSet
from subjects.views import SubjectViewSet
from periods.views import PeriodViewSet
from enrollment.views import EnrollmentViewSet
from grade_sheets.views import GradeSheetViewSet, ReportCardPrintView
from academic_years.views import AcademicYearViewSet
from pass_and_failed.views import PassFailedStatusViewSet

router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='student')
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'grades', GradeViewSet, basename='grade')
router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')
router.register(r'levels', LevelViewSet, basename='level')
router.register(r'periods', PeriodViewSet, basename='period')
router.register(r'grade_sheets', GradeSheetViewSet, basename='grade_sheets')
router.register(r'academic_years', AcademicYearViewSet, basename='academic_year')
router.register(r'pass_failed_statuses', PassFailedStatusViewSet, basename='pass_failed_status')

urlpatterns = [
    path('grade_sheets/report_card/print/', ReportCardPrintView.as_view(), name='report-card-print'),
] + router.urls

i'm satisfy with it, lets move to levels.
from django.db import models

class Level(models.Model):
    name = models.CharField(max_length=13)

    def __str__(self):
        return self.get_name_display()

    class Meta:
        ordering = ['name']

from rest_framework import serializers
from .models import Level

class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = '__all__'

from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from rest_framework.response import Response
from levels.models import Level
from levels.serializers import LevelSerializer

class LevelViewSet(viewsets.ModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer

helper:
from .models import Level

def get_all_levels():
    """Fetch all levels."""
    return Level.objects.all()

def get_level_by_id(level_id):
    """Fetch a level by ID."""
    try:
        return Level.objects.get(id=level_id)
    except Level.DoesNotExist:
        return None

def get_level_by_name(name):
    """Fetch a level by name (if you add a name field)."""
    try:
        return Level.objects.get(name=name)
    except Level.DoesNotExist:
        return None

def create_level(name):
    """Create a new level."""
    return Level.objects.create(name=name)

def update_level(level_id, new_name=None):
    """Update a level's name."""
    try:
        level = Level.objects.get(id=level_id)
        if new_name:
            level.name = new_name
        level.save()
        return level
    except Level.DoesNotExist:
        raise ValueError(f"Level with ID {level_id} does not exist.")

def delete_level(level_id):
    """Delete a level by ID."""
    try:
        level = Level.objects.get(id=level_id)
        level.delete()
        return True
    except Level.DoesNotExist:
        return False


i'm satisfy with it, lets move on to subjects.
from django.db import models
from levels.models import Level

class Subject(models.Model):
    subject = models.CharField(max_length=50)
    level = models.ForeignKey(Level, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('subject', 'level')
        ordering = ['subject', 'level']

    def __str__(self):
        return f"{self.subject} ({self.level})"

from rest_framework import serializers
from subjects.models import Subject

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'subject']

from django.shortcuts import render
import logging
# Create your views here.
from rest_framework import viewsets
from rest_framework.response import Response
from subjects.models import Subject
from subjects.serializers import SubjectSerializer
from .helper import get_subjects_by_level, delete_subject
logger = logging.getLogger(__name__)

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

    def destroy(self, request, id=None):
        """
        DELETE /api/subjects/{id}/
        Delete a subject by ID, only if no grades are associated.
        """
        try:
            subject = get_subjects_by_level(id)
            if not subject:
                logger.warning(f"Subject with id {id} not found")
                return Response({"error": f"Subject with id {IndentationError} not found"}, status=status.HTTP_404_NOT_FOUND)

           

            if delete_subject(id):
                logger.info(f"Deleted period: {id}")
                return Response({"message": f"Subject {id} deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
            else:
                logger.error(f"Failed to delete period {id}")
                return Response({"error": "Failed to delete period"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Error deleting subject {NotImplemented}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

helper:from .models import Subject

def get_subjects_by_level(level_id):
    """Fetch subjects by level and return as a dictionary {id: subject_name}."""
    subjects = Subject.objects.filter(level_id=level_id)
    return {s.id: s.subject for s in subjects}

def create_subject(subject_name, level_id):
    """Create a subject for a given level if it doesn't exist."""
    from levels.models import Level
    try:
        level = Level.objects.get(id=level_id)
    except Level.DoesNotExist:
        raise ValueError(f"Level with id {level_id} does not exist.")
    subject, created = Subject.objects.get_or_create(subject=subject_name, level=level)
    return subject, created

def update_subject(subject_id, new_name=None, new_level_id=None):
    """Update subject name and/or level."""
    try:
        subject = Subject.objects.get(id=subject_id)
        if new_name:
            subject.subject = new_name
        if new_level_id:
            from levels.models import Level
            level = Level.objects.get(id=new_level_id)
            subject.level = level
        subject.save()
        return subject
    except Subject.DoesNotExist:
        raise ValueError(f"Subject with id {subject_id} does not exist.")

def delete_subject(subject_id):
    """Delete a subject by its id."""
    try:
        subject = Subject.objects.get(id=subject_id)
        subject.delete()
        return True
    except Subject.DoesNotExist:
        return False

i'm satisfy with it, let's move to periods.
from django.db import models

class Period(models.Model):
    PERIOD_CHOICE = [
        ('1st', '1st period'),
        ('2nd', '2nd period'),
        ('3rd', '3rd period'),
        ('1exam', '1 semester exam'),
        ('4th ', '4th period'),
        ('5th ', '5th period'),
        ('6th ', '6th period'),
        ('2exam', '2 semester exam'),
    ]
    period = models.CharField(
        max_length=9, choices=PERIOD_CHOICE,
        unique=True, default='1st period'
    )
    is_exam = models.BooleanField(default=False)
   

    def __str__(self):
        return self.period

from rest_framework import serializers
from .models import Period

class PeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Period
        fields = '__all__'


import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from grades.models import Grade
from .models import Period
from .serializers import PeriodSerializer
from .helpers import get_all_periods, get_period_by_id

logger = logging.getLogger(__name__)

class PeriodViewSet(viewsets.ViewSet):
    """
    A ViewSet for managing periods, including listing, retrieving, creating, and deleting.
    """
    def list(self, request):
        """
        GET /api/periods/
        Fetch all periods.
        """
        try:
            periods = get_all_periods()
            serializer = PeriodSerializer(periods, many=True)
            logger.debug(f"Fetched {len(periods)} periods")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching periods: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, pk=None):
        """
        GET /api/periods/{id}/
        Fetch a specific period by ID.
        """
        try:
            period = get_period_by_id(pk)
            if not period:
                logger.warning(f"Period with id {pk} not found")
                return Response({"error": f"Period with id {pk} not found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = PeriodSerializer(period)
            logger.debug(f"Fetched period: {period.period}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching period {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

helper:
from .models import Period

def get_all_periods():
    """Fetch all periods."""
    return Period.objects.all()

def get_period_by_id(period_id):
    """Fetch a specific period by ID."""
    try:
        return Period.objects.get(id=period_id)
    except Period.DoesNotExist:
        return None

def create_period(period_code, is_exam=False):
    """Create a new period (e.g. '1st', '2exam')."""
    period, created = Period.objects.get_or_create(
        period=period_code,
        defaults={'is_exam': is_exam}
    )
    return period, created

def update_period(period_id, new_code=None, new_is_exam=None):
    """Update the code or exam status of a period."""
    try:
        period = Period.objects.get(id=period_id)
        if new_code:
            period.period = new_code
        if new_is_exam is not None:
            period.is_exam = new_is_exam
        period.save()
        return period
    except Period.DoesNotExist:
        raise ValueError(f"Period with id {period_id} does not exist.")

def delete_period(period_id):
    """Delete a period by ID."""
    try:
        period = Period.objects.get(id=period_id)
        period.delete()
        return True
    except Period.DoesNotExist:
        return False


i'm satisfy with it, lets move to pass_and_failed.
from django.db import models
from students.models import Student
from levels.models import Level
from academic_years.models import AcademicYear
from enrollment.models import Enrollment

class PassFailedStatus(models.Model):
    STATUS_CHOICES = (
        ('PASS', 'Pass'),
        ('FAIL', 'Failed'),
        ('CONDITIONAL', 'Pass Under Condition'),
        ('INCOMPLETE', 'Incomplete'),
        ('PENDING', 'Pending'),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='pass_failed_statuses')
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='INCOMPLETE')
    validated_at = models.DateTimeField(null=True, blank=True)
    validated_by = models.CharField(max_length=100, null=True, blank=True)
    template_name = models.CharField(max_length=100, blank=True)
    grades_complete = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'level', 'academic_year')

    def __str__(self):
        return f"{self.student} - {self.level} - {self.academic_year} - {self.status}"

    def save(self, *args, **kwargs):
        if self.status == 'PASS':
            self.template_name = 'yearly_card_pass.docx'
        elif self.status == 'FAIL':
            self.template_name = 'yearly_card_fail.docx'
        elif self.status == 'CONDITIONAL':
            self.template_name = 'yearly_card_conditional.docx'
        else:
            self.template_name = ''
        super().save(*args, **kwargs)

from rest_framework import serializers
from .models import PassFailedStatus
from students.serializers import StudentSerializer
from levels.serializers import LevelSerializer
from academic_years.serializers import AcademicYearSerializer
from enrollment.serializers import EnrollmentSerializer

class PassFailedStatusSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    level = LevelSerializer(read_only=True)
    academic_year = AcademicYearSerializer(read_only=True)
    enrollment = EnrollmentSerializer(read_only=True, allow_null=True)

    class Meta:
        model = PassFailedStatus
        fields = ['id', 'student', 'level', 'academic_year', 'enrollment', 'status',
                  'validated_at', 'validated_by', 'template_name', 'grades_complete']


import logging
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import PassFailedStatusSerializer
from .models import PassFailedStatus
from academic_years.models import AcademicYear
from .helper import handle_validate_status, initialize_missing_statuses
from grade_sheets.yearly_pdf_utils import generate_yearly_gradesheet_pdf
from grade_sheets.models import GradeSheetPDF

logger = logging.getLogger(__name__)

class PassFailedStatusViewSet(viewsets.ModelViewSet):
    queryset = PassFailedStatus.objects.all()
    serializer_class = PassFailedStatusSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        level_id = self.request.query_params.get('level_id')
        academic_year = self.request.query_params.get('academic_year')

        if level_id and academic_year:
            try:
                initialize_missing_statuses(level_id, academic_year, logger)
                academic_year_obj = AcademicYear.objects.get(name=academic_year)
                queryset = queryset.filter(level_id=level_id, academic_year=academic_year_obj)
            except AcademicYear.DoesNotExist:
                logger.error(f"Academic year {academic_year} not found")
                return PassFailedStatus.objects.none()

        return queryset

    @action(detail=True, methods=['POST'], url_path='validate')
    def validate_status(self, request, pk=None):
        logger.debug(f"Validating status for pk={pk}, data={request.data}")
        return handle_validate_status(self, request, pk, logger)

    @action(detail=True, methods=['POST'], url_path='print')
    def print_status(self, request, pk=None):
        try:
            status_obj = self.get_object()
            logger.debug(f"Printing status for pk={pk}, student={status_obj.student.id}, level={status_obj.level.id}")

            pass_template = status_obj.status in ['PASS', 'CONDITIONAL']
            pdf_paths = generate_yearly_gradesheet_pdf(
                level_id=status_obj.level.id,
                student_id=status_obj.student.id,
                pass_template=pass_template,
                academic_year=status_obj.academic_year.name
            )

            if not pdf_paths:
                logger.warning(f"No PDF generated for student {status_obj.student.id}")
                return Response({"error": "No PDF generated"}, status=status.HTTP_404_NOT_FOUND)

            pdf_path = pdf_paths[0]
            pdf_filename = os.path.basename(pdf_path)
            GradeSheetPDF.objects.update_or_create(
                level_id=status_obj.level.id,
                student_id=status_obj.student.id,
                academic_year=status_obj.academic_year,
                defaults={
                    'pdf_path': pdf_path,
                    'filename': pdf_filename,
                }
            )

            view_url = f"{settings.MEDIA_URL}output_gradesheets/{pdf_filename}"
            logger.info(f"Generated PDF for student {status_obj.student.id}: {pdf_path}")
            return Response({
                "message": "PDF generated successfully",
                "view_url": view_url,
                "pdf_path": pdf_path
            })

        except Exception as e:
            logger.error(f"Error printing status {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


utils:
from grade_sheets.helpers import get_grade_sheet_data
from subjects.models import Subject
from grades.models import Grade
from enrollment.models import Enrollment
from levels.models import Level
from academic_years.models import AcademicYear
import datetime
import logging

logger = logging.getLogger(__name__)

def validate_student_grades(student_id, level_id, academic_year_id):
    """
    Check if a student has complete grades for all subjects in a level and academic year.
    Returns: (is_complete, message)
    """
    try:
        # Fetch enrollment
        enrollment = Enrollment.objects.get(
            student_id=student_id, level_id=level_id, academic_year_id=academic_year_id
        )
        # Get grade sheet data
        grade_data = get_grade_sheet_data(student_id, level_id)
        subjects = Subject.objects.filter(level_id=level_id)
        required_periods = ['1', '2', '3', '1s', '4', '5', '6', '2s']  # Simplified periods
        required_averages = ['1a', '2a', 'f']  # Simplified averages (1a=1sa, 2a=2sa, f=fa)

        # Check if all subjects have grades
        for subject in subjects:
            subject_data = next((s for s in grade_data['s'] if s['sn'] == subject.subject), None)
            if not subject_data:
                return False, f"Missing grades for subject: {subject.subject}"
            for period in required_periods:
                if subject_data.get(period) in [None, '', '-']:
                    return False, f"Missing grade for {subject.subject} in period {period}"
            for avg in required_averages:
                if subject_data.get(avg) in [None, '', '-']:
                    return False, f"Missing {avg} average for {subject.subject}"

        return True, "All grades and averages complete"
    except Enrollment.DoesNotExist:
        return False, "No enrollment found for student"
    except Exception as e:
        logger.error(f"Error validating grades for student {student_id}: {str(e)}")
        return False, str(e)

def promote_student(status_id):
    """
    Promote a student to the next level and academic year if status is PASS or CONDITIONAL.
    Returns: (success, message)
    """
    try:
        from pass_and_failed.models import PassFailedStatus
        status = PassFailedStatus.objects.get(id=status_id)
        if status.status not in ['PASS', 'CONDITIONAL']:
            return False, "Only PASS or CONDITIONAL students can be promoted"

        current_level = status.level
        current_academic_year = status.academic_year
        student = status.student

        # Get next level
        current_level_id = int(current_level.name)  # Assuming name is '7', '8', '9'
        next_level_id = current_level_id + 1
        if next_level_id > 9:  # Max level
            return False, "Student is at the highest level (9)"

        next_level = Level.objects.filter(name=str(next_level_id)).first()
        if not next_level:
            return False, f"Next level {next_level_id} does not exist"

        # Get next academic year
        current_year = current_academic_year.name  # e.g., '2025/2026'
        start_year = int(current_year.split('/')[0]) + 1
        next_year_name = f"{start_year}/{start_year + 1}"
        next_academic_year = AcademicYear.objects.filter(name=next_year_name).first()
        if not next_academic_year:
            return False, f"Next academic year {next_year_name} does not exist"

        # Create new enrollment
        enrollment, created = Enrollment.objects.get_or_create(
            student=student,
            level=next_level,
            academic_year=next_academic_year,
            defaults={'date_enrolled': datetime.date.today()}
        )
        if created:
            logger.info(f"Promoted {student} to level {next_level}, academic year {next_academic_year}")
            return True, f"Promoted to level {next_level}, academic year {next_academic_year}"
        else:
            return False, "Enrollment already exists"
    except Exception as e:
        logger.error(f"Error promoting student {status.student}: {str(e)}")
        return False, str(e)

helper:
from rest_framework.response import Response
from rest_framework import status
from .models import PassFailedStatus
from enrollment.models import Enrollment
from academic_years.models import AcademicYear
from grades.models import Grade
from levels.models import Level
from subjects.models import Subject

def handle_validate_status(view, request, pk, logger):
    try:
        status_obj = view.get_object()
        status_value = request.data.get('status')
        validated_by = request.data.get('validated_by')

        if status_value not in ['PASS', 'FAIL', 'CONDITIONAL', 'PENDING', 'INCOMPLETE']:
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        if not status_obj.grades_complete and status_value in ['PASS', 'FAIL', 'CONDITIONAL']:
            return Response({"error": "Grades incomplete"}, status=status.HTTP_200_OK)

        status_obj.status = status_value
        status_obj.validated_by = validated_by
        status_obj.save()
        logger.info(f"Status validated: {status_obj.id} as {status_value}")

        if status_value in ['PASS', 'CONDITIONAL']:
            promote_student_if_eligible(status_obj, logger)

        serializer = view.get_serializer(status_obj)
        return Response(serializer.data)

    except Exception as e:
        logger.error(f"Error validating status {pk}: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def promote_student_if_eligible(status_obj, logger):
    current_level = status_obj.level
    next_level = Level.objects.filter(order__gt=current_level.order).order_by('order').first()

    if next_level:
        current_enrollment = Enrollment.objects.filter(
            student=status_obj.student,
            level=current_level,
            academic_year=status_obj.academic_year
        ).first()

        if current_enrollment:
            current_enrollment.status = 'PROMOTED'
            current_enrollment.save()

            Enrollment.objects.create(
                student=status_obj.student,
                level=next_level,
                academic_year=status_obj.academic_year,
                enrollment_date=status_obj.academic_year.start_date,
                status='ENROLLED'
            )
            logger.info(f"Student {status_obj.student.id} auto-promoted to level {next_level.id}")
        else:
            logger.warning(f"No current enrollment found for student {status_obj.student.id}")
    else:
        logger.warning(f"No higher level found for promotion from level {current_level.id}")

def initialize_missing_statuses(level_id, academic_year_name, logger):
    try:
        level = Level.objects.get(id=level_id)
        academic_year = AcademicYear.objects.get(name=academic_year_name)
        enrollments = Enrollment.objects.filter(level=level, academic_year=academic_year)

        for enrollment in enrollments:
            if not PassFailedStatus.objects.filter(
                student=enrollment.student,
                level=level,
                academic_year=academic_year
            ).exists():
                grades = Grade.objects.filter(enrollment=enrollment)
                subject_count = Subject.objects.filter(level=level).count()
                expected_grades = subject_count * 8 if subject_count else 1
                grades_complete = grades.exists()
                status_value = 'INCOMPLETE' if grades.count() < expected_grades else 'PENDING'

                PassFailedStatus.objects.create(
                    student=enrollment.student,
                    level=level,
                    academic_year=academic_year,
                    enrollment=enrollment,
                    grades_complete=grades_complete,
                    status=status_value,
                    template_name='pass_template.html'
                )
                logger.info(f"Created PassFailedStatus for student {enrollment.student.id}, level {level.id}, year {academic_year.name}")

        return PassFailedStatus.objects.filter(
            student__in=[e.student_id for e in enrollments]
        )

    except (Level.DoesNotExist, AcademicYear.DoesNotExist) as e:
        logger.error(f"Error filtering statuses: {str(e)}")
        return PassFailedStatus.objects.none()
    except Exception as e:
        logger.error(f"Unexpected error in initialize_missing_statuses: {str(e)}")
        return PassFailedStatus.objects.none()

i'm satisfy with it. This is the last but not the least my urls from grade_system.
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from grade_sheets.views import gradesheet_home, gradesheet_view, cors_test

urlpatterns = [
    path('api/', include('students.api')),
    path('grade_sheets/', gradesheet_home, name='gradesheet-home'),
    path('grade_sheets/view/', gradesheet_view, name='gradesheet'),
    path('admin/', admin.site.urls),
    path('api/cors-test/', cors_test, name='cors-test'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

and setting:
# grade_system/settings.py

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-ngj9d#1+k0*^0ku90narq537tx$@wdg8o$_0a0pwmdaw+#)4zk'
DEBUG = True
ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'students',
    'grades',
    'enrollment',
    'subjects',
    'levels',
    'periods',
    'grade_sheets',
    'academic_years',
    'pass_and_failed',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Moved up, before CommonMiddleware
    'django.middleware.common.CommonMiddleware',  # Only once
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_METHODS = ['GET', 'POST', 'OPTIONS', 'PUT', 'DELETE']

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

ROOT_URLCONF = 'grade_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'grade_system.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

REST_FRAMEWORK = {
    'DATE_INPUT_FORMATS': ['%Y-%m-%d'],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        # Remove 'rest_framework.renderers.BrowsableAPIRenderer' to avoid HTML responses
    ],
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
import os
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'