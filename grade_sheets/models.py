from django.db import models
from students.models import Student
from levels.models import Level
from academic_years.models import AcademicYear

class StudentGradeSheetPDF(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    pdf_path = models.CharField(max_length=255, unique=True)
    filename = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'level', 'academic_year')

    @property
    def view_url(self):
        from django.conf import settings
        return f"{settings.MEDIA_URL}{self.pdf_path}"

    def __str__(self):
        return f"{self.student} - {self.level} - {self.academic_year}"

class LevelGradeSheetPDF(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    pdf_path = models.CharField(max_length=255, unique=True)
    filename = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        unique_together = ('level', 'academic_year')

    @property
    def view_url(self):
        from django.conf import settings
        return f"{settings.MEDIA_URL}{self.pdf_path}"

    def __str__(self):
        return f"{self.level} - {self.academic_year}"