from rest_framework import viewsets, status
from rest_framework.response import Response
from grades.models import Grade
from grades.serializers import GradeSerializer
from subjects.models import Subject
from periods.models import Period
from django.core.exceptions import ValidationError
from enrollment.models import Enrollment
import logging

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
        # Handle bulk creation
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

def get_grade_map(level_id):
    """Build a grade map by student and subject."""
    grades = Grade.objects.filter(enrollment__level_id=level_id).select_related('enrollment__student', 'subject', 'period')
    print(f"Raw grades query for level {level_id}: {list(grades)}")

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
        print(f"Mapping grade: student_id={student_id}, subject_id={subject_id}, period={period}, score={score}")
        if student_id not in grade_map:
            grade_map[student_id] = {}
        if subject_id not in grade_map[student_id]:
            grade_map[student_id][subject_id] = {}
        grade_map[student_id][subject_id][period] = score
    return grade_map

def calc_semester_avg(scores, exam):
    """Calculate semester average."""
    if not scores or exam is None:
        return None
    total = sum(scores) if scores else 0
    count = len(scores)
    if exam is not None:
        total += exam
        count += 1
    return round(total / count, 2) if count > 0 else None

def calc_final_avg(sem1_avg, sem2_avg):
    """Calculate final average."""
    if sem1_avg is None or sem2_avg is None:
        return None
    return round((sem1_avg + sem2_avg) / 2, 2)

def save_grade(enrollment: Enrollment, subject_id: int, period_id: int, score: float, request) -> tuple:
    """Save or update a grade with validation."""
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