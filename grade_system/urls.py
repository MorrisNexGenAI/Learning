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
from rest_framework_simplejwt.views import TokenObtainPairView 
from rest_framework_simplejwt.views import TokenRefreshView



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
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/', admin.site.urls),
    path('api/cors-test/', cors_test, name='cors-test'),
    path('api/csrf/', get_csrf_token, name='get_csrf_token'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)