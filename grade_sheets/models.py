from django.db import models
from subjects.models import Subject
from levels.models import Level
from grades.models import Grade
from periods.models import Period
from students.models import Student


# Create your models here.
class GradeSheet(models.Model):
      student = models.ForeignKey(Student, on_delete = models.CASCADE, related_name = 'gradesheet')
      subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
      grades = models.ForeignKey(Grade, on_delete=models.CASCADE)
      level = models.ForeignKey(Level, on_delete=models.CASCADE)
      period = models.ForeignKey(Period, on_delete=models.CASCADE)
      created_at = models.DateTimeField(auto_now_add = True)

      def __str__(self):
            return f'{self.student} -{self.level} - {self.subject}-{self.period} -{self.grades}'
