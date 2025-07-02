from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from grade_sheets.views import gradesheet_home, gradesheet_view, input_grades_view, cors_test, periodic_pdf, yearly_pdf
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
router.register(r'grade_sheets', PDFGradeSheetViewSet, basename='grade_sheets')
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
    path('api/', include(router.urls)),
    path('grade_sheets/', gradesheet_home, name='gradesheet-home'),
    path('grade_sheets/view/', gradesheet_view, name='gradesheet'),
    path('api/grade_sheets/by_level/', gradesheet_view, name='gradesheet'),
    path('grade_sheets/input/', input_grades_view, name='input_grades'),
    path('grade_sheets/periodic_pdf/', periodic_pdf, name='periodic-pdf'),
    path('grade_sheets/yearly_pdf/', yearly_pdf, name='yearly-pdf'),
    path('admin/', admin.site.urls),
    path('api/cors-test/', cors_test, name='cors-test'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)