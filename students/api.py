from django.urls import path, include
from rest_framework.routers import DefaultRouter
from students.views import StudentViewSet
from levels.views import LevelViewSet
from grades.views import GradeViewSet
from subjects.views import SubjectViewSet
from periods.views import PeriodViewSet
from enrollment.views import EnrollmentViewSet
from grade_sheets.views import GradeSheetViewSet
from academic_years.views import AcademicYearViewSet
from pass_and_failed.views import PassFailedStatusViewSet, ReportCardPrintView
from pass_and_failed.views import PassFailedStatusViewSet, ReportCardPrintView

router = DefaultRouter()
router.register(r'students', StudentViewSet)
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'grades', GradeViewSet)
router.register(r'enrollments', EnrollmentViewSet)
router.register(r'levels', LevelViewSet)
router.register(r'periods', PeriodViewSet)
router.register(r'grade_sheets', GradeSheetViewSet, basename='grade_sheets')
router.register(r'academic_years', AcademicYearViewSet, basename='academic_year')
router.register(r'pass_and_failed', PassFailedStatusViewSet, basename='pass_and_failed')
router.register(r'report_cards', ReportCardPrintView, basename='report_cards')
router.register(r'pass_failed_statuses', PassFailedStatusViewSet, basename='pass_failed_status')
router.register(r'pass_failed_statuses/print', ReportCardPrintView, basename='report_card_print')

urlpatterns = [
    path('api/', include(router.urls)),
]