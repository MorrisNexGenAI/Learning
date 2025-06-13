from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from grade_sheets.views import gradesheet_home, gradesheet_view, cors_test, GradeSheetViewSet, ReportCardPrintView
from pass_and_failed.views import PassFailedStatusViewSet

router = DefaultRouter()
router.register(r'grade_sheets', GradeSheetViewSet, basename='grade_sheets')
router.register(r'pass_failed_statuses', PassFailedStatusViewSet, basename='pass_failed_statuses')

urlpatterns = [
    path('api/', include('students.api')),
    path('api/', include(router.urls)),
    path('api/grade_sheets/report_card/print/', ReportCardPrintView.as_view(), name='report-card-print'),
    path('grade_sheets/', gradesheet_home, name='gradesheet-home'),
    path('grade_sheets/view/', gradesheet_view, name='gradesheet'),
    path('admin/', admin.site.urls),
    path('api/cors-test/', cors_test, name='cors-test'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)