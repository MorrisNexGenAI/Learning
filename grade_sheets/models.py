# grade_sheets/models.py
from django.conf import settings
from django.db import models
from levels.models import Level
from students.models import Student
from academic_years.models import AcademicYear

class GradeSheetPDF(models.Model):
    pdf_path = models.CharField(max_length=512, unique=True)  # Full filesystem path
    filename = models.CharField(max_length=255)  # e.g., report_card_Jenneh_Fully_20250613_085600.pdf
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, null=True, blank=True, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('level', 'student', 'academic_year')  # Ensure one PDF per combination

    @property
    def view_url(self):
        return f"{settings.MEDIA_URL}output_gradesheets/{self.filename}"