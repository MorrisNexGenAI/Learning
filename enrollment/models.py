# enrollment/models.py
from django.db import models
from academic_years.models import AcademicYear
from students.models import Student
from levels.models import Level
import datetime


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('pass', 'Pass'),
        ('failed', 'Failed'),
        ('conditional', 'Pass Under Condition'),
        ('none', 'None'),
    ]
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name="enrollment")
    level = models.ForeignKey('levels.Level', on_delete=models.CASCADE)
    academic_year = models.ForeignKey('academic_years.AcademicYear', on_delete=models.CASCADE)
    date_enrolled = models.DateField()
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='none')

    class Meta:
        unique_together = ('student', 'level')

    def __str__(self):
        return f"{self.student} - {self.academic_year}"
