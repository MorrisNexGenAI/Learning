from rest_framework import viewsets
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .models import Student
from grade_sheets.models import GradeSheet
from subjects.models import Subject
from enrollment.models import Enrollment
from levels.models import Level
from grades.models import Grade
from .serializers import StudentSerializer
from subjects.serializers import SubjectSerializer
from enrollment.serializers import EnrollmentSerializer
from grades.serializers import GradeSerializer
from levels.serializers import LevelSerializer
from periods.serializers import PeriodSerializer
from grade_sheets.serializers import GradeSheetSerializer
from periods.models import Period

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class=StudentSerializer

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer

class LevelViewSet(viewsets.ModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer

class PeriodViewSet(viewsets.ModelViewSet):
    queryset = Period.objects.all()
    serializer_class = PeriodSerializer

class GradeSheetViewSet(viewsets.ModelViewSet):
    queryset = GradeSheet.objects.all()
    serializer_class = GradeSheetSerializer



router = DefaultRouter()
router.register(r'students', StudentViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'grades', GradeViewSet)

router.register(r'levels', LevelViewSet)
router.register(r'enrollments', EnrollmentViewSet)
router.register(r'periods', PeriodViewSet) 
router.register(r'grade_sheets', GradeSheetViewSet)

