from django.db import models

class Period(models.Model):
    PERIOD_CHOICES = [
        ('1st', '1st Period'),
        ('2nd', '2nd Period'),
        ('3rd', '3rd Period'),
        ('1exam', 'First Semester Exam'),
        ('4th', '4th Period'),
        ('5th', '5th Period'),
        ('6th', '6th Period'),
        ('2exam', 'Second Semester Exam'),
    ]

    period = models.CharField(
        max_length=10,
        choices=PERIOD_CHOICES,
        unique=True,
        default='1st'  # Set a valid default value
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.get_period_display()

        