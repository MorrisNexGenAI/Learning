from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from grade_sheets.views import gradesheet_home, gradesheet_view, input_grades_view, cors_test, GradeSheetViewSet
from grade_sheets.pdfView import GradeSheetViewSet as PDFGradeSheetViewSet
from grade_sheets.ReportCardPrintView import ReportCardPrintView
from enrollment.views import EnrollmentViewSet

router = DefaultRouter()
router.register(r'grade_sheets', GradeSheetViewSet, basename='grade_sheets')
router.register(r'grade_sheets_pdf', PDFGradeSheetViewSet, basename='grade_sheets_pdf')
router.register(r'enrollment', EnrollmentViewSet, basename='enrollment')

urlpatterns = [
    path('api/', include('students.api')),
    path('api/', include(router.urls)),
    path('grade_sheets/', gradesheet_home, name='gradesheet-home'),
    path('grade_sheets/view/', gradesheet_view, name='gradesheet'),
    path('grade_sheets/input/', input_grades_view, name='input_grades'),
    path('grade_sheets/report_card_print/', ReportCardPrintView.as_view(), name='report_card_print'),
    path('admin/', admin.site.urls),
    path('api/cors-test/', cors_test, name='cors-test'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)