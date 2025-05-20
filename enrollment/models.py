from django.db import models
from students.models import Student
from levels.models import Level
from periods.models import Period

# Create your models here.
class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollment')
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=9)
    date_enrolled = models.DateField(auto_now_add=True)
    period = models.ForeignKey('periods.Period', on_delete=models.CASCADE, default=1)  # or the id of a Period instance you want as default

  
def __str__(self):
    return f"{self.student} - {self.academic_year}"