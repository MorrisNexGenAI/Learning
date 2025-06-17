from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from grade_sheets.views import gradesheet_home, gradesheet_view, cors_test

urlpatterns = [
    path('api/', include('students.api')),
    path('grade_sheets/', gradesheet_home, name='gradesheet-home'),
    path('grade_sheets/view/', gradesheet_view, name='gradesheet'),
    path('admin/', admin.site.urls),
    path('api/cors-test/', cors_test, name='cors-test'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)