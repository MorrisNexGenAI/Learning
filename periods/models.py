from django.db import models

class Period(models.Model):
    PERIOD_CHOICE = [
        ('1st', '1st Period'),
        ('2nd', '2nd Period'),
        ('3rd', '3rd Period'),
        ('1exam', '1st Semester Exam'),
        ('4th', '4th Period'),
        ('5th', '5th Period'),
        ('6th', '6th Period'),
        ('2exam', '2nd Semester Exam'),
    ]

    period = models.CharField(
        max_length=9,
        choices=PERIOD_CHOICE,
        default='1st'
    )
    is_exam = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Automatically infer is_exam based on period value
        self.is_exam = self.period in ['1exam', '2exam']
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_period_display()