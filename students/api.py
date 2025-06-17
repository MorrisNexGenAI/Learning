from django.urls import path
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