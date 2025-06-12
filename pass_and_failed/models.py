from django.db import models
from students.models import Student
from levels.models import Level
from academic_years.models import AcademicYear
from enrollment.models import Enrollment

class PassFailedStatus(models.Model):
    STATUS_CHOICES = (
        ('PASS', 'Pass'),
        ('FAIL', 'Failed'),
        ('CONDITIONAL', 'Pass Under Condition'),
        ('INCOMPLETE', 'Incomplete'),
        ('PENDING', 'Pending'),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='pass_failed_statuses')
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='INCOMPLETE')
    validated_at = models.DateTimeField(null=True, blank=True)
    validated_by = models.CharField(max_length=100, null=True, blank=True)
    template_name = models.CharField(max_length=100, blank=True)
    grades_complete = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'level', 'academic_year')

    def __str__(self):
        return f"{self.student} - {self.level} - {self.academic_year} - {self.status}"

    def save(self, *args, **kwargs):
        if self.status == 'PASS':
            self.template_name = 'yearly_card_pass.docx'
        elif self.status == 'FAIL':
            self.template_name = 'yearly_card_fail.docx'
        elif self.status == 'CONDITIONAL':
            self.template_name = 'yearly_card_conditional.docx'
        else:
            self.template_name = ''
        super().save(*args, **kwargs)
