from django.contrib import admin
from django.urls import path, include
from grade_sheets.views import gradesheet_home, gradesheet_view, input_grades_view, cors_test

urlpatterns = [
    path('', include('students.api')),  # API routes (e.g., /api/students/, /api/grade_sheets/)
    path('grade_sheets/', gradesheet_home, name='gradesheet-home'),  # Django views
    path('grade_sheets/view/', gradesheet_view, name='gradesheet'),
    path('grade_sheets/input/', input_grades_view, name='input-grades'),
    path('admin/', admin.site.urls),
    path('api/cors-test/', cors_test, name='cors-test'),
]
