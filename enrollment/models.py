# enrollment/models.py
from django.db import models
from academic_years.models import AcademicYear
from students.models import Student
from levels.models import Level
import datetime


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    academic_year = models.ForeignKey('academic_years.AcademicYear', on_delete=models.SET_NULL, null=True)
    date_enrolled = models.DateField(default=datetime.date.today)

    class Meta:
        unique_together = ('student', 'level')

    def __str__(self):
        return f"{self.student} - {self.academic_year}"
