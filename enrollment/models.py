from django.db import models
from students.models import Student
from levels.models import Level
from academic_years.models import AcademicYear

class Enrollment(models.Model):
    ENROLLMENT_STATUS_CHOICES = (
        ('ENROLLED', 'Enrolled'),
        ('WITHDRAWN', 'Withdrawn'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollment')
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    date_enrolled = models.DateField()
    enrollment_status = models.CharField(max_length=10, choices=ENROLLMENT_STATUS_CHOICES, default='ENROLLED')

    class Meta:
        unique_together = ('student', 'level', 'academic_year')

    def __str__(self):
        return f"{self.student} - {self.level} - {self.academic_year}"