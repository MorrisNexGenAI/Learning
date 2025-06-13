# grades/models.py
from django.db import models
from enrollment.models import Enrollment
from subjects.models import Subject
from periods.models import Period

class Grade(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    score = models.FloatField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('enrollment', 'subject', 'period')

    def __str__(self):
        return f"{self.enrollment.student} - {self.subject.subject} - {self.period.period} - {self.score}"