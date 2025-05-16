from django.db import models
from enrollment.models import Enrollment
from subjects.models import Subject

# Create your models here.
class Grade(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE,related_name='grades')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.enrollment.student}-{self.subject}-{self.score}"