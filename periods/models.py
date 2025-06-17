from django.db import models

class Period(models.Model):
    PERIOD_CHOICE = [
        ('1st', '1st period'),
        ('2nd', '2nd period'),
        ('3rd', '3rd period'),
        ('1exam', '1 semester exam'),
        ('4th ', '4th period'),
        ('5th ', '5th period'),
        ('6th ', '6th period'),
        ('2exam', '2 semester exam'),
    ]
    period = models.CharField(
        max_length=9, choices=PERIOD_CHOICE,
        unique=True, default='1st period'
    )
    is_exam = models.BooleanField(default=False)
   

    def __str__(self):
        return self.period
