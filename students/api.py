from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import viewsets from each app
from students.views import StudentViewSet
from levels.views import LevelViewSet
from grades.views import GradeViewSet
from subjects.views import SubjectViewSet
from periods.views import PeriodViewSet
from enrollment.views import EnrollmentViewSet
from grade_sheets.views import GradeSheetViewSet
from academic_years.views import AcademicYearViewSet  # Add this

router = DefaultRouter()
router.register(r'students', StudentViewSet)
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'grades', GradeViewSet)
router.register(r'enrollments', EnrollmentViewSet)
router.register(r'levels', LevelViewSet)
router.register(r'periods', PeriodViewSet)
router.register(r'grade_sheets', GradeSheetViewSet, basename='grade_sheets')
router.register(r'academic_years', AcademicYearViewSet, basename='academic_year')  # Add this

urlpatterns = [
    path('api/', include(router.urls)),
]