from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from enrollment.models import Enrollment
from subjects.models import Subject
from periods.models import Period

class GradePolicy(models.Model):
    level = models.ForeignKey('levels.Level', on_delete=models.CASCADE)
    period_weight = models.FloatField(default=0.5)  # Weight for period scores
    exam_weight = models.FloatField(default=0.5)  # Weight for exam scores
    required_grades = models.IntegerField(default=8)
    passing_threshold = models.IntegerField(
        default=50,
        validators=[
            MinValueValidator(0, message="Threshold must be at least 0"),
            MaxValueValidator(100, message="Threshold cannot exceed 100")
        ]
    )

    class Meta:
        unique_together = ('level',)

    def __str__(self):
        return f"Grade Policy for {self.level}"

class Grade(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    score = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0, message="Score must be at least 0"),
            MaxValueValidator(100, message="Score cannot exceed 100")
        ]
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('enrollment', 'subject', 'period')

    def __str__(self):
        return f"{self.enrollment.student} - {self.subject} - {self.period} - {self.score}"