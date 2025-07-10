this is Level day 8

levels: This is the representation of the classroom(but digitally, hahaha). This represent each student in a specific class also call levels ex.. 7, 8, 9.
it have only one charfield models call name, which is use to store the level name.
it also have other important files call helper, serializers, and views.

models:
from django.db import models
from django.core.validators import RegexValidator

class Level(models.Model):
    name = models.CharField(
        max_length=10,
        unique=True,
        validators=[RegexValidator(r'^\d+$', message='Level name must be a number (e.g., "7" for Grade 7)')],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Grade {self.name}"

views:
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from .models import Level
from .serializers import LevelSerializer
import logging

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

class LevelViewSet(viewsets.ModelViewSet):
    queryset = Level.objects.all().order_by('name')
    serializer_class = LevelSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset

helper:
from django.core.cache import cache
from subjects.models import Subject
from .models import Level

def get_level_by_id(level_id):
    """Fetch a level by ID."""
    return Level.objects.filter(id=level_id).first()

def get_all_levels():
    """Fetch all levels, ordered by name."""
    cache_key = 'all_levels'
    levels = cache.get(cache_key)
    if levels is None:
        levels = Level.objects.all().order_by('name')
        cache.set(cache_key, levels, timeout=3600)  # Cache for 1 hour
    return levels

def get_subjects_by_level(level_id):
    """Fetch subjects for a level, with caching."""
    cache_key = f'subjects_level_{level_id}'
    subjects = cache.get(cache_key)
    if subjects is None:
        subjects = Subject.objects.filter(level_id=level_id).select_related('level')
        subjects_dict = {str(s.id): s.subject for s in subjects}
        cache.set(cache_key, subjects_dict, timeout=3600)  # Cache for 1 hour
    else:
        subjects_dict = subjects
    return subjects_dict

serializers:
from rest_framework import serializers
from .models import Level

class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ['id', 'name', 'updated_at']
        read_only_fields = ['id', 'updated_at']


this is  day 9:

subjects: These are specific courses( i couldn't say subject again so i can avoid saying the same thing twice, hahaha) that a student will have grades in for a period.
it have one Charfiled model call subject which is use to store the subject name, and a foreign key call level which is use to assigned a specific subject to a specific level.
it also have other important files call helper, models, serializers, views.

models:
from django.db import models
from django.core.validators import RegexValidator
from levels.models import Level

class Subject(models.Model):
    subject = models.CharField(
        max_length=100,
        validators=[RegexValidator(r'^[A-Z][a-zA-Z\s]*(?<!\s)$', message='Subject name must start with a capital letter and contain only letters and spaces, no trailing spaces.')],
    )
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='subjects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('subject', 'level')

    def __str__(self):
        return f"{self.subject} (Grade {self.level.name})"

views:
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from .models import Subject
from .serializers import SubjectSerializer
import logging

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all().order_by('subject')
    serializer_class = SubjectSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        level_id = self.request.query_params.get('level_id')
        search = self.request.query_params.get('search')
        if level_id:
            queryset = queryset.filter(level_id=level_id)
        if search:
            queryset = queryset.filter(subject__icontains=search)
        return queryset.select_related('level')


helper:
from django.core.cache import cache
from .models import Subject

def get_subjects_by_level(level_id):
    """Fetch subjects for a level, with caching."""
    cache_key = f'subjects_level_{level_id}'
    subjects = cache.get(cache_key)
    if subjects is None:
        subjects_qs = Subject.objects.filter(level_id=level_id).select_related('level')
        subjects = {str(s.id): s.subject for s in subjects_qs}
        cache.set(cache_key, subjects, timeout=3600)  # Cache for 1 hour
    return subjects


serializers:
from rest_framework import serializers
from .models import Subject
from levels.serializers import LevelSerializer

class SubjectSerializer(serializers.ModelSerializer):
    level = LevelSerializer(read_only=True)

    class Meta:
        model = Subject
        fields = ['id', 'subject', 'level', 'updated_at']
        read_only_fields = ['id', 'updated_at']


This is day 10, the periods:

periods:These are specific terms of the academic_year in which students received lessons and also take test at the end of each followed by a special test call exam which climax a semester made of three periods. They are divided into stable six call: 1st, 2nd,3rd,and a 1exam, then 4th, 5th,6th, and a 2exam.
it have a charfield model call period and a booleanfield model call is_exam.
it also have other important files call: helpers, serializers, views.

models:
from django.db import models

class Period(models.Model):
    PERIOD_CHOICE = [
        ('1st', '1st Period'),
        ('2nd', '2nd Period'),
        ('3rd', '3rd Period'),
        ('1exam', '1st Semester Exam'),
        ('4th', '4th Period'),
        ('5th', '5th Period'),
        ('6th', '6th Period'),
        ('2exam', '2nd Semester Exam'),
    ]

    period = models.CharField(
        max_length=9,
        choices=PERIOD_CHOICE,
        default='1st'
    )
    is_exam = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Automatically infer is_exam based on period value
        self.is_exam = self.period in ['1exam', '2exam']
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_period_display()


views:
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
    A ViewSet for managing periods.
    """

    def list(self, request):
        try:
            periods = get_all_periods()
            serializer = PeriodSerializer(periods, many=True)
            logger.debug(f"Fetched {len(periods)} periods")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching periods: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, pk=None):
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

    def destroy(self, request, pk=None):
        try:
            period = get_period_by_id(pk)
            if not period:
                return Response({"error": "Period not found."}, status=404)

            if Grade.objects.filter(period=period).exists():
                return Response({"error": "Cannot delete period linked to grades."}, status=400)

            period.delete()
            logger.info(f"Deleted period {pk}")
            return Response(status=204)
        except Exception as e:
            logger.error(f"Error deleting period {pk}: {str(e)}")
            return Response({"error": str(e)}, status=500)


helpers:
from .models import Period

VALID_PERIODS = [choice[0] for choice in Period.PERIOD_CHOICE]

def get_all_periods():
    """Fetch all periods."""
    return Period.objects.all()

def get_period_by_id(period_id):
    """Fetch a specific period by ID."""
    try:
        return Period.objects.get(id=period_id)
    except Period.DoesNotExist:
        return None

def create_period(period_code):
    """Create a new period if valid (e.g. '1st', '2exam')."""
    if period_code not in VALID_PERIODS:
        raise ValueError(f"Invalid period code: '{period_code}'.")
    period, created = Period.objects.get_or_create(
        period=period_code
    )
    return period, created

def update_period(period_id, new_code=None):
    """Update the code of a period if valid."""
    try:
        period = Period.objects.get(id=period_id)
        if new_code:
            if new_code not in VALID_PERIODS:
                raise ValueError(f"Invalid period code: '{new_code}'.")
            period.period = new_code
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


serilizers:
from rest_framework import serializers
from .models import Period

class PeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Period
        fields = '__all__'


This is day 11: pass and failed:


pass_and_failed:I guess you already know what this does from the name alone, hahaha. This is what use to determine whether a student will be promoted to another level or not. I guess you think it is more codes again, but the acutal reason that brought this model in was to help teachers or admiistrators connect what word template the app should use to display a specific student grade so that it can be generated as a pdf. it link the templates for the students based on whether they pass or failed or pass under condition.
it have a long list of choices:STATUS_CHOICES = (
        ('PASS', 'Pass'),
        ('FAIL', 'Failed'),
        ('CONDITIONAL', 'Pass Under Condition'),
        ('INCOMPLETE', 'Incomplete'),
        ('PENDING', 'Pending'),
    )
with many foreign keys and charfields, booleanfields. They are so many that i'm gonna paste because i can't afford to write all:student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='pass_failed_statuses')
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='INCOMPLETE')
    validated_at = models.DateTimeField(null=True, blank=True)
    validated_by = models.CharField(max_length=100, null=True, blank=True)
    template_name = models.CharField(max_length=100, blank=True)
    grades_complete = models.BooleanField(default=False)
i hope you can understand and explain them too(maybe that's an assignment for whoever reading this).


models:
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

Views.py:
import logging
import os
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import PassFailedStatusSerializer
from .models import PassFailedStatus
from academic_years.models import AcademicYear
from .helper import handle_validate_status, initialize_missing_statuses
from grade_sheets.yearly_pdf import generate_yearly_pdf
from grade_sheets.models import StudentGradeSheetPDF

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

        return queryset.order_by('id')  # Ensure consistent pagination

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
            pdf_paths = generate_yearly_pdf(
                level_id=status_obj.level.id,
                student_id=status_obj.student.id,
                pass_template=pass_template,
                conditional=status_obj.status == 'CONDITIONAL',
                academic_year_id=status_obj.academic_year.id  # Use numeric ID
            )

            if not pdf_paths:
                logger.warning(f"No PDF generated for student {status_obj.student.id}")
                return Response({"error": "No PDF generated"}, status=status.HTTP_404_NOT_FOUND)

            pdf_path = pdf_paths[0]
            pdf_filename = os.path.basename(pdf_path)
            StudentGradeSheetPDF.objects.update_or_create(
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


serializers:
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

helper:
from rest_framework.response import Response
from rest_framework import status
from .models import PassFailedStatus
from enrollment.models import Enrollment
from academic_years.models import AcademicYear
from grades.models import Grade
from levels.models import Level
from subjects.models import Subject
from datetime import date, timedelta

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
    try:
        current_level = status_obj.level
        current_level_name = current_level.name
        try:
            current_level_number = int(current_level_name)  # Assume name is '1', '2', etc.
            next_level_number = current_level_number + 1
            next_level = Level.objects.filter(name=str(next_level_number)).first()
        except (ValueError, TypeError):
            logger.warning(f"Level name {current_level_name} is not numeric, cannot promote")
            return

        if not next_level:
            logger.warning(f"No higher level found for promotion from level {current_level.id}")
            return

        # Get or create the next academic year
        current_academic_year = status_obj.academic_year
        try:
            current_year = int(current_academic_year.name.split('/')[0])
            next_year = current_year + 1
            next_academic_year_name = f"{next_year}/{next_year + 1}"
            next_academic_year, created = AcademicYear.objects.get_or_create(
                name=next_academic_year_name,
                defaults={
                    'start_date': date(next_year, 9, 1),
                    'end_date': date(next_year + 1, 6, 30)
                }
            )
            if created:
                logger.info(f"Created new AcademicYear: {next_academic_year_name}")
        except (ValueError, TypeError):
            logger.error(f"Cannot parse academic year {current_academic_year.name} for promotion")
            return

        current_enrollment = Enrollment.objects.filter(
            student=status_obj.student,
            level=current_level,
            academic_year=current_academic_year
        ).first()

        if current_enrollment:
            # Check if enrollment for next level and next academic year exists
            next_enrollment = Enrollment.objects.filter(
                student=status_obj.student,
                level=next_level,
                academic_year=next_academic_year
            ).first()

            if next_enrollment:
                logger.info(f"Enrollment already exists for student {status_obj.student.id} at level {next_level.id}, academic_year {next_academic_year.name}")
                # Update existing enrollment
                next_enrollment.enrollment_status = 'ENROLLED'
                next_enrollment.save()
            else:
                # Create new enrollment for next level and next academic year
                Enrollment.objects.create(
                    student=status_obj.student,
                    level=next_level,
                    academic_year=next_academic_year,
                    date_enrolled=next_academic_year.start_date,
                    enrollment_status='ENROLLED'
                )
                logger.info(f"Student {status_obj.student.id} auto-promoted to level {next_level.id}, academic_year {next_academic_year.name}")

            # Update PassFailedStatus
            status_obj.status = 'PASS' if status_obj.status == 'PASS' else 'CONDITIONAL'
            status_obj.save()
        else:
            logger.warning(f"No current enrollment found for student {status_obj.student.id}")
    except Exception as e:
        logger.error(f"Error promoting student {status_obj.student.id}: {str(e)}")

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


This is day 12: AcademicYear:
models:
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from datetime import datetime

class AcademicYear(models.Model):
    name = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(r'^\d{4}/\d{4}$', message='Name must be in the format "YYYY/YYYY" (e.g., "2024/2025")')],
    )
    start_date = models.DateField()
    end_date = models.DateField()

    def clean(self):
        """Validate that end_date is after start_date and matches name years."""
        if self.end_date <= self.start_date:
            raise ValidationError('End date must be after start date.')
        if self.name:
            start_year, end_year = map(int, self.name.split('/'))
            if self.start_date.year != start_year or self.end_date.year != end_year:
                raise ValidationError('Start and end dates must match the years in the name.')
            if end_year != start_year + 1:
                raise ValidationError('End year must be one year after start year.')

    def save(self, *args, **kwargs):
        self.full_clean()  # Run clean() before saving
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-start_date']

Views:
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from .models import AcademicYear
from .serializers import AcademicYearSerializer
import logging
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.all().order_by('-start_date')
    serializer_class = AcademicYearSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        cache_key = 'academic_years_queryset'
        queryset = cache.get(cache_key)
        if queryset is None:
            queryset = super().get_queryset()
            is_active = self.request.query_params.get('is_active')
            name = self.request.query_params.get('name')
            if is_active == 'true':
                today = timezone.now().date()
                queryset = queryset.filter(start_date__lte=today, end_date__gte=today)
            if name:
                queryset = queryset.filter(name__icontains=name)
            cache.set(cache_key, queryset, timeout=3600)  # Cache for 1 hour
        return queryset

helpers:
from django.utils import timezone
from django.core.cache import cache
from .models import AcademicYear

def get_all_academic_years():
    """Return all academic years, cached."""
    cache_key = 'all_academic_years'
    years = cache.get(cache_key)
    if years is None:
        years = AcademicYear.objects.all()
        cache.set(cache_key, years, timeout=3600)  # Cache for 1 hour
    return years

def get_academic_year_by_id(year_id):
    """Return a specific academic year by ID."""
    try:
        return AcademicYear.objects.get(id=year_id)
    except AcademicYear.DoesNotExist:
        return None

def get_academic_year_by_name(name):
    """Return academic year by name (e.g., '2024/2025')."""
    try:
        return AcademicYear.objects.get(name=name)
    except AcademicYear.DoesNotExist:
        return None

def get_current_academic_year():
    """Return the academic year containing today's date."""
    cache_key = 'current_academic_year'
    year = cache.get(cache_key)
    if year is None:
        today = timezone.now().date()
        year = AcademicYear.objects.filter(start_date__lte=today, end_date__gte=today).first()
        cache.set(cache_key, year, timeout=3600)  # Cache for 1 hour
    return year

def create_academic_year(name, start_date, end_date):
    """Create a new academic year."""
    return AcademicYear.objects.create(name=name, start_date=start_date, end_date=end_date)

def update_academic_year(year_id, name=None, start_date=None, end_date=None):
    """Update an existing academic year."""
    try:
        year = AcademicYear.objects.get(id=year_id)
        if name:
            year.name = name
        if start_date:
            year.start_date = start_date
        if end_date:
            year.end_date = end_date
        year.save()
        return year
    except AcademicYear.DoesNotExist:
        raise ValueError(f"Academic year with ID {year_id} does not exist.")

def delete_academic_year(year_id):
    """Delete an academic year."""
    try:
        year = AcademicYear.objects.get(id=year_id)
        year.delete()
        return True
    except AcademicYear.DoesNotExist:
        return False

serializers:
from rest_framework import serializers
from .models import AcademicYear

class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ['id', 'name', 'start_date', 'end_date']
        read_only_fields = ['id']



This is day 13 the grade_system;

settings.py:
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
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']


CORS_ALLOW_CREDENTIALS = True

CSRF_COOKIE_HTTPONLY = False  # Ensure JavaScript can read the CSRF cookie
CSRF_COOKIE_SECURE = False

REST_FRAMEWORK = {
    'DATE_INPUT_FORMATS': ['%Y-%m-%d'],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100
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

urls.py:
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from grade_sheets.views import GradeSheetViewSet, gradesheet_home, input_grades_view, cors_test, periodic_pdf, yearly_pdf, get_csrf_token, gradesheet_view
from grade_sheets.pdfView import GradeSheetViewSet as PDFGradeSheetViewSet
from enrollment.views import EnrollmentViewSet
from students.views import StudentViewSet
from levels.views import LevelViewSet
from grades.views import GradeViewSet
from subjects.views import SubjectViewSet
from periods.views import PeriodViewSet
from academic_years.views import AcademicYearViewSet
from pass_and_failed.views import PassFailedStatusViewSet

router = DefaultRouter()
router.register(r'grade_sheets', GradeSheetViewSet, basename='grade_sheets')
router.register(r'grade_sheets_pdf', PDFGradeSheetViewSet, basename='grade_sheets_pdf')
router.register(r'enrollment', EnrollmentViewSet, basename='enrollment')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'grades', GradeViewSet, basename='grade')
router.register(r'levels', LevelViewSet, basename='level')
router.register(r'periods', PeriodViewSet, basename='period')
router.register(r'academic_years', AcademicYearViewSet, basename='academic_year')
router.register(r'pass_failed_statuses', PassFailedStatusViewSet, basename='pass_failed_status')

urlpatterns = [
    path('api/', include(router.urls)),  # DRF routes for /api/grade_sheets/
    path('grade_sheets/input/', input_grades_view, name='input_grades'),
    path('grade_sheets/periodic_pdf/', periodic_pdf, name='periodic-pdf'),
    path('grade_sheets/yearly_pdf/', yearly_pdf, name='yearly-pdf'),
    path('api/grade_sheets/home/', gradesheet_home, name='gradesheet-home'),  # Renamed to avoid conflict
    path('api/grade_sheets/view/', gradesheet_view, name='gradesheet'),
    path('admin/', admin.site.urls),
    path('api/cors-test/', cors_test, name='cors-test'),
    path('api/csrf/', get_csrf_token, name='get_csrf_token'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


Day 14 is a general Review of the entire backend, and questions about what was learn and recap.

put each day into it own word documents